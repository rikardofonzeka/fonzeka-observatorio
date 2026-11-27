(() => {
  const root=document.querySelector('[data-dof-catalog]');if(!root)return;
  const $=id=>root.querySelector('#'+id),cards=$('dof-cards'),status=$('dof-status'),filters=$('dof-filters'),search=$('dof-search'),institution=$('dof-institution'),year=$('dof-year'),month=$('dof-month'),day=$('dof-day');
  const norm=s=>String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const text=(p,tag,value,cls)=>{const x=document.createElement(tag);x.textContent=value;if(cls)x.className=cls;p.append(x);return x;};
  const link=(p,value,url,primary=false,external=false)=>{const a=text(p,'a',value,'dof-button'+(primary?' primary':''));a.href=url;if(external){a.target='_blank';a.rel='noopener noreferrer';}return a;};
  const empty=(title,message)=>{const box=text(cards,'div','','dof-empty');text(box,'h3',title);text(box,'p',message);};
  const base=new URL(root.dataset.dofCatalog,document.baseURI);let docs=[];
  function validOfficial(value,code){try{const u=new URL(value);return u.protocol==='https:'&&((u.hostname==='sidof.segob.gob.mx'&&['/notas/'+code,'/notas/docFuente/'+code].includes(u.pathname))||(u.hostname==='dof.gob.mx'&&u.pathname==='/nota_detalle.php'&&u.searchParams.get('codigo')===code));}catch{return false;}}
  const months=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
  const unique=values=>[...new Set(values)].sort();
  function setOptions(select,values,all,label=v=>v){
    const previous=select.value;
    select.replaceChildren(new Option(all,''));
    for(const v of values)select.add(new Option(label(v),v));
    select.value=values.includes(previous)?previous:'';
    select.disabled=values.length===0;
  }
  function updateDates(){
    const eligible=docs.filter(d=>!institution.value||d.institucion===institution.value);
    setOptions(year,unique(eligible.map(d=>d.fecha_dof.slice(0,4))).reverse(),'Todos los años');
    const byYear=eligible.filter(d=>!year.value||d.fecha_dof.slice(0,4)===year.value);
    setOptions(month,unique(byYear.map(d=>d.fecha_dof.slice(5,7))),'Todos los meses',v=>months[Number(v)-1]);
    const byMonth=month.value?byYear.filter(d=>d.fecha_dof.slice(5,7)===month.value):[];
    setOptions(day,unique(byMonth.map(d=>d.fecha_dof.slice(8,10))),'Todos los días');
  }
  function render(){cards.replaceChildren();const q=norm(search.value),inst=institution.value,y=year.value,m=month.value,dd=day.value;const matches=docs.filter(d=>(!inst||d.institucion===inst)&&(!y||d.fecha_dof.slice(0,4)===y)&&(!m||d.fecha_dof.slice(5,7)===m)&&(!dd||d.fecha_dof.slice(8,10)===dd)&&(!q||norm([d.titulo,d.tema,d.codigo_dof,d.institucion,d.resumen].join(' ')).includes(q)));
    status.textContent=matches.length+' de '+docs.length+' expedientes publicados';
    if(!docs.length){empty('Aún no hay expedientes publicados','El catálogo se actualizará cuando un expediente de las fuentes institucionales supere la verificación editorial y esté disponible para consulta.');return;}
    if(!matches.length){empty('No hay coincidencias','Prueba otro término, institución o fecha.');return;}
    for(const d of matches){const c=text(cards,'article','','dof-card'),m=text(c,'div','','dof-meta');for(const label of [d.institucion,d.fecha_dof,'DOF '+d.codigo_dof])text(m,'span',label,'dof-tag');text(c,'h3',d.titulo);text(c,'div',d.tema,'dof-kicker');text(c,'p',d.resumen);const links=text(c,'div','','dof-links');const u=new URL('expediente.html',base);u.searchParams.set('codigo',d.codigo_dof);link(links,'Consultar expediente',u.href,true);if(validOfficial(d.url_oficial,d.codigo_dof))link(links,'Original DOF',d.url_oficial,false,true);}
  }
  fetch(base,{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(data=>{if(data.schema!==2||!Array.isArray(data.expedientes))throw Error();if(data.expedientes.some(d=>!/^\d{7}$/.test(d.codigo_dof)||!/^\d{4}-\d{2}-\d{2}$/.test(d.fecha_dof)||!['titulo','institucion','tema','resumen'].every(k=>typeof d[k]==='string')||!validOfficial(d.url_oficial,d.codigo_dof)))throw Error();docs=data.expedientes.sort((a,b)=>b.fecha_dof.localeCompare(a.fecha_dof)||b.codigo_dof.localeCompare(a.codigo_dof));for(const v of [...new Set(docs.map(d=>d.institucion))].sort())institution.add(new Option(v,v));updateDates();filters.hidden=false;render();}).catch(()=>{status.textContent='No se pudo consultar el catálogo.';status.classList.add('dof-error');cards.replaceChildren();empty('Consulta temporalmente no disponible','Actualiza la página para volver a intentarlo.');});
  search.addEventListener('input',render);for(const select of [institution,year,month])select.addEventListener('change',()=>{updateDates();render();});day.addEventListener('change',render);
})();
