const toolbar=document.createElement('nav');
toolbar.className='blank-toolbar';
toolbar.setAttribute('aria-label','Редагування бланка');
toolbar.innerHTML='<a href="index.html">Усі бланки</a><button type="button" data-add-row>Додати товар</button><button type="button" data-remove-row>Прибрати останній</button><button type="button" data-print>Друкувати / PDF</button><span>Натисніть на поле, щоб змінити текст.</span>';
document.body.prepend(toolbar);
const editorStyles=document.createElement('style');
editorStyles.textContent='.blank-toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:14px;background:#17171a;color:white;position:sticky;top:0;z-index:10}.blank-toolbar button,.blank-toolbar a{background:#ffcc00;color:#17171a;border:0;border-radius:5px;padding:10px;text-decoration:none;cursor:pointer;font:600 13px Arial}.blank-toolbar span{font:12px Arial}[contenteditable=true]:focus{outline:2px solid #ffcc00} @media print{.blank-toolbar{display:none!important}body{background:white;print-color-adjust:exact;-webkit-print-color-adjust:exact}.s{width:100%;min-height:277mm;margin:0;padding:0}tr{break-inside:avoid}[contenteditable=true]{outline:none!important}}';
document.head.append(editorStyles);
const formatter=new Intl.NumberFormat('uk-UA',{minimumFractionDigits:2,maximumFractionDigits:2});
const valueOf=t=>Number(String(t).replace(/\s/g,'').replace(',','.').replace(/[^\d.-]/g,''))||0;
function recalculate(){let total=0;document.querySelectorAll('tbody tr').forEach((row,index)=>{row.cells[0].textContent=index+1;const quantity=Math.max(0,valueOf(row.cells[2].textContent));const price=Math.max(0,valueOf(row.cells[3].textContent));const amount=quantity*price;row.cells[4].textContent=formatter.format(amount);total+=amount});document.querySelector('.total').innerHTML=`Разом: ${formatter.format(total)} грн`}
document.querySelectorAll('.dh h1,.meta,.f,.note,.wf div,.legal,.sign div,tbody td:nth-child(2),tbody td:nth-child(3),tbody td:nth-child(4)').forEach(element=>{element.contentEditable='true';element.spellcheck=true});
document.querySelector('[data-add-row]').addEventListener('click',()=>{const row=document.querySelector('tbody').insertRow();row.innerHTML='<td></td><td contenteditable="true">Назва товару або послуги</td><td contenteditable="true">1</td><td contenteditable="true">0,00</td><td>0,00</td>';recalculate()});
document.querySelector('[data-remove-row]').addEventListener('click',()=>{const rows=document.querySelectorAll('tbody tr');if(rows.length>1)rows[rows.length-1].remove();recalculate()});
document.querySelector('[data-print]').addEventListener('click',()=>window.print());
document.addEventListener('input',recalculate);recalculate();
