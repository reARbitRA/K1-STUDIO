// # SPEC-004
import { useEffect, useRef, useState } from 'react';
import { Activity, ArrowDownToLine, AudioLines, ChevronDown, Disc3, FolderOpen, Headphones, Layers3, Pause, Play, Plus, Radio, Redo2, Scissors, Settings2, SkipBack, Undo2, Volume2, Waves } from 'lucide-react';
import { store, effects, initialProject, type Project, type Effect, type Master } from './store';
import { Transport, wavBlob } from './audio';
import { Wave } from './Wave';
const colors=['#06b6d4','#e7a759','#b49afa','#e16b89','#7cbe87','#7ba2ef','#b7c460','#e5a6da'];
const names=['Hard mute','NASA radio','Underwater','Tape stop','Stutter','40 Hz sub drop'];
const descriptions=['Clean silence. No clicks.','Narrow-band transmission','Deep low-pass immersion','Decelerating analog brake','Loop, drift, degrade','Phase-locked bass impact'];
const clock=(s:number)=>`${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toFixed(3).padStart(6,'0')}`;
async function json<T>(path:string, init?:RequestInit):Promise<T>{
  const res=await fetch(path,init);if(!res.ok){const e=await res.json().catch(()=>null);throw new Error(e?.error?.message||`Request failed (${res.status})`);}return res.json() as Promise<T>;
}
function Field({label,value,min,max,step=.1,onChange}:{label:string;value:number;min:number;max:number;step?:number;onChange:(v:number)=>void}){
  const id=label.replaceAll(' ','-');return <label className="field" htmlFor={id}><span>{label}</span><div><input aria-label={`${label} slider`} type="range" min={min} max={max} step={step} value={value} onPointerDown={()=>store.getState().begin()} onPointerUp={()=>store.getState().commit()} onChange={e=>onChange(Number(e.target.value))}/><input id={id} type="number" min={min} max={max} step={step} value={value} onChange={e=>{const v=e.target.valueAsNumber;if(Number.isFinite(v)&&v>=min&&v<=max)onChange(v);}}/></div></label>;
}
export default function App(){
  const state=store();const project=state.project;const [selected,setSelected]=useState('');
  const [target,setTarget]=useState('track');const [activeRegion,setActiveRegion]=useState<string|null>(null);const [start,setStart]=useState(4.12),[end,setEnd]=useState(4.88);
  const [wet,setWet]=useState(1),[fade,setFade]=useState(8);const [time,setTime]=useState(0),[duration,setDuration]=useState(12);
  const [levels,setLevels]=useState<Record<string,number>>({});
  const [playing,setPlaying]=useState(false),[busy,setBusy]=useState(''),[error,setError]=useState('');
  const [status,setStatus]=useState('Your next mix starts here.'),[download,setDownload]=useState('');
  const [telemetry,setTelemetry]=useState<{before:{integrated_lufs:number|null};after:{integrated_lufs:number|null;true_peak_dbtp:number|null}}|null>(null);
  const [bypass,setBypass]=useState(false),[strip,setStrip]=useState(false);
  const transport=useRef(new Transport()),file=useRef<HTMLInputElement>(null),audition=useRef<HTMLAudioElement|null>(null);
  const track=project.tracks.find(t=>t.track_id===selected)||project.tracks[0];
  async function run(label:string, action:()=>Promise<void>){setBusy(label);setError('');try{await action();}catch(e){setError(e instanceof Error?e.message:'Operation failed');}finally{setBusy('');}}
  useEffect(()=>{store.getState().restore();},[]);
  useEffect(()=>{let dead=false;if(!project.tracks.length)return;
    transport.current.prepare(project).then(()=>{if(!dead)setDuration(transport.current.duration);}).catch(e=>{if(!dead)setError(String(e));});
    return()=>{dead=true;};
  },[project]);
  useEffect(()=>{let frame:number;const tick=()=>{const t=transport.current.time();setTime(t);setLevels(transport.current.levels());
    if(transport.current.playing&&t>=transport.current.duration){transport.current.stop();setPlaying(false);}frame=requestAnimationFrame(tick);};
    frame=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame);
  },[]);
  useEffect(()=>{if(!transport.current.playing)return;transport.current.stop();transport.current.play(project).catch(e=>{setError(String(e));setPlaying(false);});},[project]);
  async function ingest(files:File[],demo=false){
    let graph=demo?initialProject():structuredClone(project);
    for(let i=0;i<files.length;i++){
      const form=new FormData();form.append('file',files[i]);if(graph.project_id)form.append('project_id',graph.project_id);
      const data=await json<{project:Project;duration_sec:number}>('/api/v1/ingest/upload',{method:'POST',body:form});
      const added=data.project.tracks.filter(t=>!graph.tracks.some(old=>old.track_id===t.track_id));
      graph={...data.project,...(graph.project_id?{master_bus:graph.master_bus,bpm:graph.bpm}:{}),tracks:[...graph.tracks,...added]};
      if(demo)graph.tracks.at(-1)!.name=['SYNTH 01','BASS 02','DRUMS 03','TEXTURE 04'][i];
    }
    state.load(graph);setSelected(graph.tracks[0]?.track_id||'');setStatus(`${files.length} audio ${files.length===1?'file':'files'} imported · 48 kHz / float32`);
  }
  async function demo(){
    const files=[220,55,110,660].map((hz,index)=>{const data=new Float32Array(48000*12);
      for(let n=0;n<data.length;n++){const t=n/48000;data[n]=.14*Math.sin(2*Math.PI*hz*t)*(index===2?Math.exp(-(t%0.5)*25):.65+.35*Math.sin(t*3));}
      return new File([wavBlob(data)],`demo-${index}.wav`,{type:'audio/wav'});});
    await ingest(files,true);
  }
  async function split(mode:'2stem'|'4stem'){
    if(!track)throw new Error('Import a track first.');
    const data=await json<{job_id:string;websocket_url:string}>('/api/v1/ingest/split-stems',{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_id:project.project_id,track_id:track.track_id,mode})});
    await new Promise<void>((resolve,reject)=>{const ws=new WebSocket(`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}${data.websocket_url}`);
      ws.onmessage=event=>{const e=JSON.parse(event.data);setStatus(`${e.stage} · ${Math.round(e.progress*100)}%`);
        if(e.status==='failed'){reject(new Error(e.error?.error?.message||'Separation failed'));ws.close();}
        if(e.status==='succeeded'){const p=e.project as Project;const known=new Set(project.tracks.map(t=>t.track_id));
          const stems=p.tracks.filter(t=>!known.has(t.track_id));store.getState().edit(g=>{const i=g.tracks.findIndex(t=>t.track_id===track.track_id);g.tracks.splice(i,1,...stems);});resolve();ws.close();}};
      ws.onerror=()=>reject(new Error('Separation connection failed'));ws.onclose=e=>{if(e.code!==1000)reject(new Error('Separation connection closed'));};
    });
  }
  function apply(effect:Effect){if(!track){setError('Import a track before creating a region.');return;}
    if(start<0||end>duration||end-start<2/48000){setError('Region bounds must fit the audio and span at least two samples.');return;}
    const r={region_id:crypto.randomUUID(),start_sec:start,end_sec:end,effect_type:effect,wet_mix:wet,fade_ms:effect==='HARD_MUTE'?3:fade};
    state.edit(p=>{const regions=target==='master'?p.master_bus.regions:p.tracks.find(t=>t.track_id===track.track_id)!.regions;const old=regions.findIndex(x=>x.region_id===activeRegion);if(old>=0)regions[old]={...r,region_id:activeRegion!};else regions.push(r);});
    setStatus(`${names[effects.indexOf(effect)]} applied · ${start.toFixed(3)}–${end.toFixed(3)} s`);
  }
  async function preview(){
    const regions=target==='master'?project.master_bus.regions:track?.regions;const region=regions?.at(-1);
    if(!region)throw new Error('Apply a region preset to audition it.');
    transport.current.stop();setPlaying(false);audition.current?.pause();
    const res=await fetch('/api/v1/preview/region',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:structuredClone(project),target_type:target,track_id:target==='master'?null:track?.track_id,region_id:region.region_id,bypass_master:bypass})});
    if(!res.ok){const e=await res.json();throw new Error(e.error.message);}
    const url=URL.createObjectURL(await res.blob());const player=new Audio(url);audition.current=player;
    player.onended=()=>URL.revokeObjectURL(url);await player.play();setStatus(bypass?'Auditioning pre-master mix':'Auditioning authoritative region + master render');
  }
  async function exportAudio(){
    if(!project.tracks.length)throw new Error('Import audio before exporting.');
    const result=await json<{downloads:{url:string}[];telemetry:NonNullable<typeof telemetry>}>('/api/v1/project/render',{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(structuredClone(project))});
    setDownload(result.downloads[0].url);setTelemetry(result.telemetry);setStatus('Master verified · 24-bit WAV ready to download');
  }
  function master(key:keyof Omit<Master,'regions'|'mono_bass_cutoff_hz'|'ceiling_db'>,v:number){state.edit(p=>{p.master_bus[key]=v;});}
  const activeRegions=target==='master'?project.master_bus.regions:track?.regions||[];
  return <div className="studio bg-studio text-slate-200">
    <aside className="rail"><div className="rail-logo">K<span>1</span></div><button className="active" aria-label="Mixer"><AudioLines size={20}/></button><button aria-label="Select audio files" onClick={()=>file.current?.click()}><FolderOpen size={19}/></button><button aria-label="Show channel strip" onClick={()=>setStrip(!strip)}><Settings2 size={19}/></button><div className="rail-bottom"><Headphones size={18}/><span>LOCAL</span></div></aside>
    <main><header><div className="brand"><h1>K1<span>STUDIO</span><i> / </i></h1><div><strong>Untitled session</strong><span>NON-DESTRUCTIVE AUDIO WORKSTATION</span></div></div><div className="engine"><i/> DSP ENGINE <b>48k</b><span>32-BIT FLOAT</span></div><button className="icon-button" aria-label="Demo session" onClick={()=>run('Loading demo',demo)} disabled={!!busy}><Disc3 size={16}/> Try demo</button></header>
    <section className="transport" aria-label="Transport">
      <div className="imports"><input type="file" accept=".wav,.flac,.aif,.aiff" multiple hidden ref={file} onChange={e=>{const files=Array.from(e.target.files||[]);if(files.length)run('Importing',()=>ingest(files));e.target.value='';}}/><button onClick={()=>file.current?.click()} disabled={!!busy}><Plus size={16}/> Import audio</button><span className="divider"/><button className="subtle" onClick={()=>run('Separating',()=>split('2stem'))} disabled={!!busy||!track}><Layers3 size={14}/>2-stem</button><button className="subtle" onClick={()=>run('Separating',()=>split('4stem'))} disabled={!!busy||!track}>4-stem</button></div>
      <div className="playback"><button className="icon-button" aria-label="Return to start" onClick={()=>{transport.current.seek(0);setPlaying(false);}}><SkipBack size={17}/></button><button className="play-button" aria-label={playing?'Pause':'Play'} disabled={!track} onClick={()=>run('Starting playback',async()=>{if(playing){transport.current.stop();setPlaying(false);}else{audition.current?.pause();await transport.current.play(project);setPlaying(true);}})}>{playing?<Pause size={17}/>:<Play size={17}/>}</button><output className="timecode">{clock(time)}</output><span className="time-unit">MIN : SEC</span></div>
      <div className="exports"><button className="icon-button" aria-label="Undo" disabled={!state.past.length} onClick={state.undo}><Undo2 size={16}/></button><button className="icon-button" aria-label="Redo" disabled={!state.future.length} onClick={state.redo}><Redo2 size={16}/></button><span className="divider"/><button onClick={()=>run('Rendering preview',preview)} disabled={!!busy||!track}><Headphones size={14}/> Preview region</button><button className="primary" onClick={()=>run('Mastering',exportAudio)} disabled={!!busy}><ArrowDownToLine size={15}/> Export WAV</button></div>
    </section>
    <section className="session-bar"><div><span className="eyebrow">SESSION</span><b>{project.tracks.length.toString().padStart(2,'0')}</b> TRACKS <span className="session-name">/ SURGICAL MIX</span></div><div className="session-tools"><span>STEREO</span><span>48,000 Hz</span><span className="accent-dot"/>AUTOSAVED LOCALLY</div></section>
    <section className="arrangement" aria-label="Track arrangement"><div className="timeline"><span>TRACK / CHANNEL</span><div><input type="range" aria-label="Seek timeline" min={0} max={duration} step={.01} value={Math.min(time,duration)} onChange={e=>{transport.current.seek(Number(e.target.value));setPlaying(false);}}/>{[0,.25,.5,.75,1].map(v=><label key={v}>{clock(v*duration)}</label>)}</div></div>
      <div className="track-scroll">{project.tracks.map((t,i)=><div key={t.track_id} className={`track-row ${track?.track_id===t.track_id?'selected':''}`} style={{'--track':colors[i%8]} as React.CSSProperties}>
        <div className="track-head" onClick={()=>setSelected(t.track_id)}><div className="track-title"><span className="track-number">{String(i+1).padStart(2,'0')}</span><AudioLines size={15}/><strong>{t.name}</strong><span className="track-indicator"/></div><div className="track-controls">{(['mute','solo','phase_invert'] as const).map((key,j)=><button key={key} className={t[key]?'toggled':''} aria-label={`${['Mute','Solo','Invert phase'][j]} ${t.name}`} aria-pressed={t[key]} onClick={()=>state.edit(p=>{const current=p.tracks.find(a=>a.track_id===t.track_id)!;current[key]=!current[key];})}>{['M','S','Ø'][j]}</button>)}<span className="track-type">STEREO</span></div><div className="track-level"><label>GAIN <input aria-label={`Gain ${t.name}`} type="number" min={-24} max={12} step={.1} value={t.gain_db} onChange={e=>{const n=e.target.valueAsNumber;if(Number.isFinite(n)&&n>=-24&&n<=12)state.edit(p=>{p.tracks.find(x=>x.track_id===t.track_id)!.gain_db=n;});}}/>dB</label><label>PAN<input aria-label={`Pan ${t.name}`} type="range" min={-1} max={1} step={.01} value={t.pan} onPointerDown={state.begin} onPointerUp={state.commit} onChange={e=>state.edit(p=>{p.tracks.find(x=>x.track_id===t.track_id)!.pan=Number(e.target.value);})}/></label></div><div className="track-meter" aria-label={`Level ${t.name}`}><i style={{width:`${(levels[t.track_id]||0)*100}%`}}/></div></div>
        <div className="wave-cell"><Wave track={t} color={colors[i%8]} time={time} audio={transport.current.buffers.get(t.file_path)} duration={duration} onSelect={(a,b,id)=>{setSelected(t.track_id);setStart(a);setEnd(b);setTarget('track');setActiveRegion(id||null);const r=t.regions.find(r=>r.region_id===id);if(r){setWet(r.wet_mix);setFade(r.fade_ms);}}} onRegion={(id,a,b)=>state.edit(p=>{const r=p.tracks.find(x=>x.track_id===t.track_id)?.regions.find(x=>x.region_id===id);if(r){r.start_sec=a;r.end_sec=b;}})}/></div>
      </div>)}{!project.tracks.length&&<div className="empty"><div className="empty-symbol"><Waves size={35}/></div><h2>Make room for a better mix.</h2><p>Import your stems. Shape a moment. Find your sound.</p><button onClick={()=>file.current?.click()}><Plus size={15}/> Import WAV, FLAC or AIFF</button><small>Local processing. Original audio stays untouched.</small></div>}</div>
    </section>
    <section className="lower"><div className="inspector"><div className="panel-title"><Scissors size={16}/><h2>Surgical regions</h2><span>REGION DSP</span><button className="icon-button" aria-label="Toggle channel strip" onClick={()=>setStrip(!strip)}><Settings2 size={15}/></button></div>
    {strip&&track?<div className="strip-grid">{Object.entries(track.channel_strip).map(([key,value])=>{const ranges:Record<string,number[]>={hp_hz:[20,500],de_mud_db:[-6,3],presence_db:[-6,6],de_fizz_db:[-6,0],comp_threshold_db:[-40,0],comp_ratio:[1,10],comp_attack_ms:[1,100],comp_release_ms:[20,500]};return <Field key={key} label={key.replaceAll('_',' ')} value={value} min={ranges[key]?.[0]??-40} max={ranges[key]?.[1]??500} onChange={v=>state.edit(p=>{p.tracks.find(x=>x.track_id===track.track_id)!.channel_strip[key]=v;})}/>;})}</div>:<>
      <div className="selection"><span>SELECTION</span><label>IN <input aria-label="Region start seconds" type="number" min={0} step={.001} value={start} onChange={e=>setStart(e.target.valueAsNumber||0)}/></label><span className="selection-arrow">→</span><label>OUT <input aria-label="Region end seconds" type="number" min={0} step={.001} value={end} onChange={e=>setEnd(e.target.valueAsNumber||0)}/></label><output>{Math.max(0,end-start).toFixed(3)} s</output></div>
      <div className="target"><span>APPLY TO</span><select aria-label="Region target" value={target} onChange={e=>setTarget(e.target.value)}><option value="track">{track?.name||'Selected track'}</option><option value="master">All tracks · master bus</option></select><ChevronDown size={13}/></div>
      <div className="preset-grid">{effects.map((effect,i)=><button key={effect} aria-label={names[i]} onClick={()=>apply(effect)} className={activeRegions.at(-1)?.effect_type===effect?'preset-active':''}><span className="preset-icon">{i===0?<Volume2 size={16}/>:i===1?<Radio size={16}/>:i===2?<Waves size={16}/>:i===3?<Disc3 size={16}/>:i===4?<AudioLines size={16}/>:<Activity size={16}/>}</span><span><strong>{names[i]}</strong><small>{descriptions[i]}</small></span></button>)}</div>
      <div className="region-bottom"><label>WET <input aria-label="Region wet mix" type="range" min={0} max={1} step={.01} value={wet} onChange={e=>setWet(Number(e.target.value))}/><b>{Math.round(wet*100)}%</b></label><label>FADE <input aria-label="Region fade milliseconds" type="number" min={2} max={15} step={1} value={fade} onChange={e=>{const v=e.target.valueAsNumber;if(v>=2&&v<=15)setFade(v);}}/>ms</label><span>{activeRegions.at(-1)?.effect_type||'ZERO-CROSSING ENABLED'}</span></div></>}
    </div><div className="master"><div className="panel-title"><Activity size={16}/><h2>Analog mastering</h2><span>MASTER BUS</span><button className={`bypass ${bypass?'on':''}`} aria-label="A/B bypass master" aria-pressed={bypass} onClick={()=>setBypass(!bypass)}>A / B <i/></button></div>
      <div className="master-top"><span className="mono"><i/>MONO SUB <b>&lt;85 Hz</b></span><Field label="Stereo width" value={project.master_bus.stereo_width} min={0} max={1.5} step={.01} onChange={v=>master('stereo_width',v)}/></div>
      <div className="eq-grid">{([['LOW','62 Hz','pultec_low_boost_db'],['DE-MUD','285 Hz','mud_cut_db'],['PRESENCE','2.7 kHz','mid_bite_db'],['AIR','10.5 kHz','air_boost_db']] as const).map(([label,hz,key])=><label className="dial-control" key={key}><span>{label}</span><div className="dial"><input aria-label={label+' EQ'} type="range" min={-12} max={12} step={.1} value={project.master_bus[key]} onPointerDown={state.begin} onPointerUp={state.commit} onChange={e=>master(key,Number(e.target.value))}/><div className="knob"><i style={{transform:`rotate(${project.master_bus[key]*8}deg)`}}/></div></div><input aria-label={label+' dB'} type="number" min={-12} max={12} step={.1} value={project.master_bus[key]} onChange={e=>{const v=e.target.valueAsNumber;if(v>=-12&&v<=12)master(key,v);}}/><small>{hz}</small></label>)}</div>
      <div className="master-macros"><Field label="Parallel crush" value={project.master_bus.parallel_comp_mix} min={0} max={1} step={.01} onChange={v=>master('parallel_comp_mix',v)}/><Field label="Tape drive" value={project.master_bus.tape_drive} min={1} max={2} step={.01} onChange={v=>master('tape_drive',v)}/></div>
      <div className="loudness"><label>TARGET LOUDNESS<select aria-label="Target loudness" value={project.master_bus.target_lufs} onChange={e=>master('target_lufs',Number(e.target.value))}><option value={-14}>-14.0 LUFS · Streaming</option><option value={-9.5}>-9.5 LUFS · Club master</option><option value={-8}>-8.0 LUFS · Aggressive</option></select></label><div><span>TRUE PEAK</span><strong>{telemetry?.after.true_peak_dbtp?.toFixed(2)||'−0.3'} <small>dBTP {telemetry?'MEASURED':'CEILING'}</small></strong></div></div>
    </div></section>
    <footer><span className={error?'error-status':'status-dot'}/><span role={error?'alert':'status'}>{error||busy||status}</span>{download&&<a href={download} download>Download verified WAV <ArrowDownToLine size={12}/></a>}<div><span>LOCAL-FIRST</span><i>·</i><span>{telemetry?.after.integrated_lufs?.toFixed(1)||'--'} LUFS</span><i>·</i>PCM 24-BIT <span className="version">K1 / 0.1</span></div></footer>
    </main></div>;
}
