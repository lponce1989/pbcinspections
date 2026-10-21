// Progressive enhancement: check age, sortable price columns, filters. Page works without JS.
(function(){
  var today=new Date();
  document.querySelectorAll('time.ago').forEach(function(t){
    var d=new Date(t.getAttribute('datetime')+'T12:00:00');
    if(isNaN(d))return;
    var n=Math.floor((today-d)/864e5);
    t.textContent=(n<=0?'today':n===1?'1 day ago':n+' days ago')+' ('+t.getAttribute('datetime')+')';
  });
  document.querySelectorAll('table.sortable').forEach(function(tb){
    var body=tb.tBodies[0];
    tb.querySelectorAll('th[data-sort]').forEach(function(th){
      var idx=Array.prototype.indexOf.call(th.parentNode.children,th);
      var b=document.createElement('button');b.type='button';b.textContent=th.textContent;th.textContent='';th.appendChild(b);
      b.addEventListener('click',function(){
        var asc=th.getAttribute('aria-sort')!=='ascending';
        tb.querySelectorAll('th[data-sort]').forEach(function(o){o.removeAttribute('aria-sort')});
        th.setAttribute('aria-sort',asc?'ascending':'descending');
        var rows=Array.prototype.slice.call(body.rows);
        rows.sort(function(a,c){
          var x=a.cells[idx].getAttribute('data-v'),y=c.cells[idx].getAttribute('data-v');
          if(x===''&&y==='')return 0;if(x==='')return 1;if(y==='')return -1; // unpublished prices last
          return asc?x-y:y-x;});
        rows.forEach(function(r){body.appendChild(r)});
      });
    });
  });
  // Filters apply to the table rows and the listing cards (cards are the only list on phones).
  document.querySelectorAll('.filters').forEach(function(f){
    var scope=f.closest('section')||document;
    var items=Array.prototype.slice.call(scope.querySelectorAll('table.city-table tbody tr, .cards .insp'));
    var cards=scope.querySelectorAll('.cards .insp').length;
    f.hidden=false;var cnt=f.querySelector('.count');
    var q=new URLSearchParams(location.search),on0=q.getAll('show').join(',').split(',');
    f.querySelectorAll('input').forEach(function(i){if(on0.indexOf(i.getAttribute('data-f'))>-1)i.checked=true});
    var apply=function(){
      var on=Array.prototype.filter.call(f.querySelectorAll('input'),function(i){return i.checked}).map(function(i){return i.getAttribute('data-f')});
      var shown=0;
      items.forEach(function(r){
        var ok=on.every(function(k){return r.getAttribute('data-'+k)==='1'});
        r.hidden=!ok;if(ok&&r.classList.contains('insp'))shown++;});
      cnt.textContent=shown+' of '+cards+' shown';
      var u=new URL(location.href);u.searchParams.delete('show');var qs=u.searchParams.toString();
      if(on.length)qs=(qs?qs+'&':'')+'show='+on.join(',');
      history.replaceState(null,'',u.pathname+(qs?'?'+qs:'')+u.hash);
    };
    f.addEventListener('change',apply);apply();
  });
  // Card details: always open on wide screens (CSS handles browsers with ::details-content)
  if(window.matchMedia('(min-width:701px)').matches)document.querySelectorAll('details.more').forEach(function(d){d.open=true});
})();
