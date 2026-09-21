(() => {
  'use strict';
  if (/\/admin(?:\/|\.html|$)/.test(location.pathname)) return;
  const id = 'G-55NS10JRQV', key = 'altcam-analytics-consent';
  let enabled = false;
  const read = () => { try { return localStorage.getItem(key); } catch { return null; } };
  function start() {
    if (enabled) return;
    enabled = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('consent', 'default', {analytics_storage:'granted',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
    window.gtag('js', new Date());
    window.gtag('config', id, {send_page_view:false,allow_google_signals:false,allow_ad_personalization_signals:false});
    window.gtag('event','page_view',{page_location:location.origin+location.pathname,page_title:document.title,page_referrer:document.referrer?new URL(document.referrer).origin:''});
    const script=document.createElement('script');script.async=true;
    script.src='https://www.googletagmanager.com/gtag/js?id='+id;document.head.append(script);
  }
  const names = {product_details:'view_item',add_to_cart:'add_to_cart',checkout_completed:'generate_lead',consultation_sent:'generate_lead',click_phone:'contact_click',click_telegram:'contact_click',price_request_started:'price_request'};
  window.altcamAnalytics = (event, data={}) => {
    if (!enabled || !names[event]) return;
    const params={page_location:location.origin+location.pathname};
    if (event.startsWith('click_')) params.method=event==='click_phone'?'phone':'telegram';
    if (/^(?:yugtorg|viatec)-[\w-]+$/.test(String(data.id||''))) params.items=[{item_id:String(data.id)}];
    window.gtag('event',names[event],params);
  };
  function choose(value) {
    try { localStorage.setItem(key,value); } catch {}
    panel.hidden=true;
    if(value==='yes')start();
    else if(enabled){window.gtag('consent','update',{analytics_storage:'denied'});enabled=false;location.reload();}
  }
  const style=document.createElement('style');style.textContent='.ga-consent{position:fixed;bottom:16px;left:16px;max-width:420px;background:#202024;color:#fff;padding:18px;border:1px solid #fc0;border-radius:10px;z-index:9999;font:14px/1.5 Arial}.ga-consent[hidden]{display:none}.ga-consent button{margin:8px 8px 0 0;padding:9px;border:1px solid #fc0;background:#fc0;color:#111;cursor:pointer}.ga-consent a{color:#fc0}.ga-settings{position:fixed;bottom:4px;left:4px;z-index:9998;font:11px Arial}';document.head.append(style);
  const panel=document.createElement('section');panel.className='ga-consent';panel.setAttribute('aria-label','Налаштування аналітики');
  panel.innerHTML='<p>Дозволити Google Analytics вимірювати відвідування та перегляди товарів? Це необов’язково. <a href="/privacy-policy.html">Конфіденційність</a></p><button type="button" data-yes>Дозволити</button><button type="button" data-no>Відхилити</button>';
  document.body.append(panel);panel.querySelector('[data-yes]').onclick=()=>choose('yes');panel.querySelector('[data-no]').onclick=()=>choose('no');
  const settings=document.createElement('button');settings.type='button';settings.className='ga-settings';settings.textContent='Налаштування cookies';settings.onclick=()=>{panel.hidden=false;};document.body.append(settings);
  panel.hidden=read()!==null;if(read()==='yes')start();
})();
