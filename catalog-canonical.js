// Query variants are UI states, not new indexable pages. Keep the cart URL intact.
(function(root){
  function canonicalPath(search,products){
    const id=new URLSearchParams(search).get('product');
    const item=id&&(products||[]).find(p=>String(p.id)===id);
    return item&&/^\/products\/[a-z0-9-]+\/$/.test(item.page_url||'')?item.page_url:'/catalog.html';
  }
  if(typeof module!=='undefined')module.exports={canonicalPath};
  if(!root.document)return;
  const url='https://alt-cam.net.ua'+canonicalPath(root.location.search,root.ALTCAM_CATALOG);
  let link=root.document.querySelector('link[rel="canonical"]');
  if(!link){link=root.document.createElement('link');link.rel='canonical';root.document.head.append(link);}
  link.href=url;
  const og=root.document.querySelector('meta[property="og:url"]');if(og)og.content=url;
})(typeof window==='undefined'?globalThis:window);
