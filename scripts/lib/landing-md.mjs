export const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const pending=/\[(?:ЗАПОВНИТИ|ПІДТВЕРДИТИ)[^\]]*\]/;
export function parseLanding(source){
 const match=source.replace(/\r/g,'').match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);if(!match)throw Error('Missing landing frontmatter');
 const meta={};for(const line of match[1].split('\n')){const m=line.match(/^(\w+):\s*(.*)$/);if(!m)continue;let value=m[2].split('  #')[0].trim();meta[m[1]]=value.startsWith('[')?value.slice(1,-1).split(',').map(x=>x.trim()):value;}
 if(!/^[a-z0-9-]+$/.test(meta.slug||''))throw Error('Unsafe landing slug');
 for(const key of ['title','description','h1'])if(!meta[key]||pending.test(meta[key]))throw Error(`Missing metadata: ${key}`);
 const sections=[];let current={title:'',body:[]};sections.push(current);
 for(const line of match[2].split('\n')){if(line.startsWith('## ')){current={title:line.slice(3),body:[]};sections.push(current);}else if(!/^# /.test(line))current.body.push(line);}
 return {meta,sections};
}
export function inline(source){
 return escape(source).replace(/\[([^\]]+)\]\(([^\s)]+)\)/g,(_,label,url)=>/^(?:\/(?!\/)|https:\/\/|tel:)/.test(url)?`<a href="${url}">${label}</a>`:label).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/`([^`]+)`/g,'<code>$1</code>');
}
export function markdown(source,{production=true,omitted=[],table=()=>'',photo=()=>''}={}){
 let html='';const blocks=source.trim().split(/\n\s*\n/);
 for(let block of blocks){
  if(!block.trim())continue;
  if(pending.test(block)){omitted.push(block);if(production){if(/^\s*(?:-|\d+\.) /m.test(block))block=block.split('\n').filter(line=>!pending.test(line)).join('\n');else continue;}else{html+=`<div class="content-pending">${escape(block)}</div>`;continue;}}
  block=block.replace(/\[ВСТАВИТИ ТАБЛИЦЮ[^\]]*\]/g,directive=>`\n\n@@TABLE:${[...new Set(directive.match(/T[1-5]/g)||[])].join(',')}\n\n`).replace(/\[ВСТАВИТИ ФОТО:[^\]]*\]/g,directive=>`\n\n@@PHOTO:${directive}\n\n`);
  for(const part of block.split(/\n\s*\n/)){
   if(part.startsWith('@@TABLE:')){html+=part.slice(8).split(',').map(table).join('');continue;}
   if(part.startsWith('@@PHOTO:')){html+=photo(part.slice(8));continue;}
   if(part.startsWith('>'))continue;
   if(part.startsWith('|')){const rows=part.split('\n').filter(l=>!/^\|[\s:|-]+\|$/.test(l)).map(l=>l.replace(/^\||\|$/g,'').split('|').map(x=>x.trim()));html+='<div class="table-scroll" tabindex="0" role="region" aria-label="Таблиця"><table>'+rows.map((r,i)=>'<tr>'+r.map(c=>`<${i?'td':'th'}>${inline(c)}</${i?'td':'th'}>`).join('')+'</tr>').join('')+'</table></div>';continue;}
   if(/^(?:-|\d+\.) /m.test(part)){const ordered=/^\d+\./.test(part),tag=ordered?'ol':'ul';html+=`<${tag}>`+part.split('\n').filter(Boolean).map(l=>`<li>${inline(l.replace(/^(?:-|\d+\.) /,''))}</li>`).join('')+`</${tag}>`;continue;}
   if(/^### /.test(part)){html+=`<h3>${inline(part.slice(4))}</h3>`;continue;}
   if(part.trim())html+=`<p>${inline(part.replace(/^\*\*Лід[^*]*\*\*\s*/,''))}</p>`;
  }
 }
 return html;
}
export function faqEntries(body,{omitted=[]}={}){
 return body.join('\n').split(/^### /m).slice(1).flatMap(block=>{if(pending.test(block)){omitted.push(block);return [];}const [question,...answer]=block.trim().split('\n');return [{question,answer:answer.join(' ').trim()}];});
}
