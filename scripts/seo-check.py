"""Offline build audit. No third-party packages, no HTTP requests.
Usage: python scripts/seo-check.py [_site] [--strict]
JSON contains every finding; console contains counts and representative URLs.
"""
import collections
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlsplit, unquote
import xml.etree.ElementTree as ET

ORIGIN = 'https://alt-cam.net.ua'
VOID = {'img','meta','link','input','br','hr','source','area','base','embed','wbr','col','param'}
def clean(s):
    return ' '.join(html.unescape(s).split())

class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.stack=[]; self.titles=[]; self.h1=[]; self.headings=[]; self.description=[]
        self.canon=[]; self.links=[]; self.images=[]; self.ids=set(); self.ld=[]
        self.text=[]; self.robots=''; self.redirect=False; self.capture=None; self.buf=[]
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag=='link' and a.get('rel')=='canonical': self.canon.append(a.get('href',''))
        if tag=='meta':
            if a.get('name')=='description': self.description.append(a.get('content',''))
            if a.get('name')=='robots': self.robots=a.get('content','')
            if a.get('http-equiv','').lower()=='refresh': self.redirect=True
        if tag=='a' and 'href' in a: self.links.append((a['href'],any(t in ('nav','footer') for t in self.stack)))
        if tag=='img': self.images.append(a)
        if tag in ['title','h1','h2','h3','h4','h5','h6'] or (tag=='script' and a.get('type')=='application/ld+json'):
            self.capture=tag; self.buf=[]
        if tag not in VOID: self.stack.append(tag)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_data(self,data):
        if self.capture: self.buf.append(data)
        if not any(t in ('script','style','head') for t in self.stack): self.text.append(data)
    def handle_endtag(self,tag):
        if tag==self.capture:
            value=clean(''.join(self.buf))
            if tag=='title': self.titles.append(value)
            elif tag=='script': self.ld.append(''.join(self.buf))
            else:
                self.headings.append((int(tag[1]),value))
                if tag=='h1': self.h1.append(value)
            self.capture=None; self.buf=[]
        if tag in self.stack: self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]

def nodes(obj):
    if isinstance(obj,dict):
        if '@type' in obj: yield obj
        for v in obj.values(): yield from nodes(v)
    elif isinstance(obj,list):
        for v in obj: yield from nodes(v)

def audit(root, progress=False):
    root=Path(root).resolve(); issues=[]; pages={}; skipped=[]
    def add(kind,url,detail): issues.append({'kind':kind,'url':url,'detail':detail})
    @lru_cache(maxsize=None)
    def target(route):
        p=root/unquote(route).lstrip('/')
        if p.is_dir(): p=p/'index.html'
        return p
    @lru_cache(maxsize=None)
    def exists(file):
        return file.is_relative_to(root) and file.exists()
    def read(file):
        return file,Page(file.read_text(encoding='utf-8'))
    files=[]
    for file in root.rglob('*.html'):
        rel=file.relative_to(root).as_posix()
        if rel.startswith(('assets/','social-posts/')): skipped.append(rel); continue
        files.append(file)
    with ThreadPoolExecutor(max_workers=8) as pool:
        for file,page in pool.map(read,files):
            rel=file.relative_to(root).as_posix();route='/'+re.sub(r'(^|/)index\.html$',r'\1',rel)
            if page.redirect or 'noindex' in page.robots or rel.startswith(('admin','blanks/')): skipped.append(rel); continue
            pages[route]=page
            if progress and len(pages)%1000==0: print('Parsed',len(pages),'pages',flush=True)
    robotfile=root/'robots.txt'; rules=[]
    if not robotfile.exists(): add('robots_missing','/robots.txt','missing')
    else:
        robots=robotfile.read_text(encoding='utf-8')
        if 'Sitemap: '+ORIGIN+'/sitemap.xml' not in robots: add('robots_sitemap','/robots.txt','missing canonical sitemap')
        active=False
        for raw in robots.splitlines():
            line=raw.split('#')[0].strip()
            if ':' not in line: continue
            key,val=[x.strip() for x in line.split(':',1)]
            if key.lower()=='user-agent': active=val=='*'
            if active and key.lower() in ('allow','disallow') and val: rules.append((key.lower(),val))
    def blocked(route):
        matches=[]
        for kind,pattern in rules:
            rx='^'+re.escape(pattern).replace(r'\*','.*').replace(r'\$','$')
            if re.search(rx,route): matches.append((len(pattern.replace('*','')),kind=='allow'))
        return bool(matches) and not max(matches)[1]
    fields={k:collections.defaultdict(list) for k in ('title','h1','description')}
    for page_number,(route,p) in enumerate(pages.items(),1):
        if progress and page_number%1000==0: print('Checked',page_number,'pages',flush=True)
        for field,values in [('title',p.titles),('h1',p.h1),('description',p.description)]:
            if len(values)!=1 or not clean(values[0]): add(field+'_count',route,len(values))
            elif values[0]: fields[field][clean(values[0])].append(route)
        if len(p.canon)!=1: add('canonical_count',route,p.canon)
        elif p.canon[0]!=ORIGIN+route: add('canonical_mismatch',route,p.canon[0])
        if blocked(route): add('robots_blocks_page',route,'indexable HTML blocked')
        level=0
        for n,text in p.headings:
            if n>level+1: add('heading_jump',route,f'H{level} → H{n}: {text}')
            level=n
        for img in p.images:
            if not img.get('alt','').strip(): add('empty_alt',route,img.get('src',''))
        for href,nav in p.links:
            if href=='#' and nav: add('navigation_hash',route,href)
            if not href or href=='#': continue
            u=urlsplit(urljoin(ORIGIN+route,href))
            if u.scheme not in ('http','https') or u.netloc!=urlsplit(ORIGIN).netloc: continue
            f=target(u.path)
            if not exists(f): add('broken_link',route,href)
            elif u.fragment and u.path in pages and unquote(u.fragment) not in pages[u.path].ids:
                add('missing_anchor',route,href)
        typed=[]
        for text in p.ld:
            try: typed.extend(nodes(json.loads(text)))
            except ValueError as e: add('invalid_json_ld',route,str(e))
        types={t for n in typed for t in (n['@type'] if isinstance(n['@type'],list) else [n['@type']])}
        if route=='/' and not types.intersection({'LocalBusiness','HomeAndConstructionBusiness'}): add('missing_business',route,'LocalBusiness subtype')
        if route.startswith('/products/') and 'Product' not in types: add('missing_product',route,'Product')
        for n in typed:
            if n.get('@type')=='FAQPage':
                visible=clean(' '.join(p.text))
                for q in n.get('mainEntity',[]):
                    if clean(q.get('name','')) not in visible or clean(q.get('acceptedAnswer',{}).get('text','')) not in visible: add('faq_not_visible',route,q.get('name'))
    for kind,mapping in fields.items():
        for value,urls in mapping.items():
            if len(urls)>1: add('duplicate_'+kind,urls[0],{'value':value,'urls':urls})
    sitemap=set(); visited=set()
    def read_map(file):
        if file in visited: return
        visited.add(file)
        try: doc=ET.parse(file).getroot()
        except (OSError,ET.ParseError) as e: add('invalid_sitemap','/sitemap.xml',str(e));return
        ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
        if doc.tag not in (ns+'urlset',ns+'sitemapindex'): add('invalid_sitemap','/sitemap.xml','namespace/root');return
        for entry in doc:
            loc=entry.findtext(ns+'loc',''); u=urlsplit(loc)
            if u.scheme!='https' or u.netloc!='alt-cam.net.ua' or u.query or u.fragment: add('sitemap_url','/sitemap.xml',loc);continue
            f=target(u.path)
            if doc.tag==ns+'sitemapindex':
                if f.is_relative_to(root): read_map(f)
            else:
                if loc in sitemap: add('sitemap_duplicate',loc,loc)
                sitemap.add(loc)
                if u.path not in pages: add('sitemap_nonindexable',u.path,loc)
                if blocked(u.path): add('sitemap_blocked',u.path,loc)
    read_map(root/'sitemap.xml')
    for route in pages:
        if ORIGIN+route not in sitemap: add('sitemap_missing',route,'indexable page absent')
    counts=dict(collections.Counter(x['kind'] for x in issues))
    return {'pages':len(pages),'sitemap_urls':len(sitemap),'skipped':skipped,'counts':counts,'issues':issues}

if __name__=='__main__':
    root=next((x for x in sys.argv[1:] if not x.startswith('--')),'_site')
    result=audit(root,progress=True);out=Path('outputs/seo-audit');out.mkdir(parents=True,exist_ok=True)
    (out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[f"Pages: {result['pages']}; sitemap URLs: {result['sitemap_urls']}"]
    for kind,count in result['counts'].items():
        sample=[x['url'] for x in result['issues'] if x['kind']==kind][:3]
        lines.append(f'{kind}: {count}; examples: '+', '.join(sample))
    if not result['issues']: lines.append('Clean audit.')
    (out/'summary.txt').write_text('\n'.join(lines),encoding='utf-8')
    print('\n'.join(lines));print('Full report: outputs/seo-audit/report.json')
    if '--strict' in sys.argv and result['issues']: sys.exit(1)
