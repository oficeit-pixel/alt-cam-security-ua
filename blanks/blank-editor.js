const formatter=new Intl.NumberFormat('uk-UA',{minimumFractionDigits:2,maximumFractionDigits:2});
const valueOf=t=>Number(String(t).replace(/\s/g,'').replace(',','.').replace(/[^\d.-]/g,''))||0;
function recalculate(){let total=0;document.querySelectorAll('tbody tr').forEach((row,index)=>{row.cells[0].textContent=index+1;const quantity=Math.max(0,valueOf(row.cells[2].textContent));const price=Math.max(0,valueOf(row.cells[3].textContent));const amount=quantity*price;row.cells[4].textContent=formatter.format(amount);total+=amount});document.querySelector('.total').innerHTML=`Разом: ${formatter.format(total)} грн`}
document.querySelectorAll('.dh h1,.meta,.f,.note,.wf div,.legal,.sign div,tbody td:nth-child(2),tbody td:nth-child(3),tbody td:nth-child(4)').forEach(element=>{element.contentEditable='true';element.spellcheck=true});
document.querySelector('[data-add-row]').addEventListener('click',()=>{const row=document.querySelector('tbody').insertRow();row.innerHTML='<td></td><td contenteditable="true">Назва товару або послуги</td><td contenteditable="true">1</td><td contenteditable="true">0,00</td><td>0,00</td>';recalculate()});
document.querySelector('[data-remove-row]').addEventListener('click',()=>{const rows=document.querySelectorAll('tbody tr');if(rows.length>1)rows[rows.length-1].remove();recalculate()});
document.querySelector('[data-print]').addEventListener('click',()=>window.print());
document.addEventListener('input',recalculate);recalculate();
