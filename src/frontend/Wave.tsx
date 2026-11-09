// # SPEC-004
import { useEffect, useRef } from 'react';
import WaveSurfer from 'wavesurfer.js';
import Regions from 'wavesurfer.js/dist/plugins/regions.esm.js';
import Timeline from 'wavesurfer.js/dist/plugins/timeline.esm.js';
import Minimap from 'wavesurfer.js/dist/plugins/minimap.esm.js';
import type { Track, Region } from './store';
export function Wave({track,color,time,audio,duration,onSelect,onRegion}:{track:Track;color:string;time:number;audio?:AudioBuffer;duration:number;onSelect:(a:number,b:number,id?:string)=>void;onRegion:(id:string,a:number,b:number)=>void}) {
  const container=useRef<HTMLDivElement>(null);const wave=useRef<WaveSurfer|null>(null);
  const callbacks=useRef({onSelect,onRegion});callbacks.current={onSelect,onRegion};
  const regions=useRef<ReturnType<typeof Regions.create>|null>(null);
  useEffect(()=>{
    const plugin=Regions.create();regions.current=plugin;
    const count=2048;const peaks=new Float32Array(count);
    if(audio){const data=audio.getChannelData(0);for(let i=0;i<count;i++){
      const a=Math.floor(i*duration*audio.sampleRate/count),b=Math.min(data.length,Math.ceil((i+1)*duration*audio.sampleRate/count));
      for(let j=a;j<b;j++)if(Math.abs(data[j])>Math.abs(peaks[i]))peaks[i]=data[j];}}
    const ws=WaveSurfer.create({container:container.current!,waveColor:color,progressColor:color,
      cursorColor:'#e9eaf0',height:54,barWidth:1.5,barGap:1,normalize:true,interact:true,
      ...(audio?{peaks:[peaks],duration}:{url:`/api/v1/assets/${track.file_path}`}),plugins:[plugin,Timeline.create({height:10}),Minimap.create({height:8,waveColor:color})]});
    wave.current=ws;ws.on('error',()=>{});plugin.enableDragSelection({color:`${color}28`});
    plugin.on('region-created',r=>{if(r.id.startsWith('region-')){callbacks.current.onSelect(r.start,r.end);r.remove();}});
    plugin.on('region-clicked',(r,event)=>{event.stopPropagation();callbacks.current.onSelect(r.start,r.end,r.id);});
    plugin.on('region-updated',r=>callbacks.current.onRegion(r.id,r.start,r.end));
    return()=>{ws.destroy();};
  },[track.file_path,color,audio,duration]);
  useEffect(()=>{wave.current?.setTime(time);},[time]);
  useEffect(()=>{
    const plugin=regions.current;if(!plugin)return;
    plugin.clearRegions();track.regions.forEach((r:Region)=>plugin.addRegion({id:r.region_id,start:r.start_sec,end:r.end_sec,color:`${color}38`,content:r.effect_type.replaceAll('_',' ')}));
  },[track.regions,color,audio,duration]);
  return <div ref={container} className="wave" aria-label={`${track.name} waveform`} />;
}
