// # SPEC-004
import type { Project } from './store';
export class Transport {
  context:AudioContext|null=null;
  buffers=new Map<string,AudioBuffer>();
  sources:AudioBufferSourceNode[]=[];
  meters=new Map<string,{node:AnalyserNode,data:Float32Array<ArrayBuffer>}>();
  startTime=0;offset=0;playing=false;duration=0;
  async prepare(project:Project) {
    this.context??=new AudioContext();
    for(const t of project.tracks)if(!this.buffers.has(t.file_path)){
      const res=await fetch(`/api/v1/assets/${encodeURIComponent(t.file_path)}`);
      if(!res.ok)throw new Error('Audio asset is no longer available. Import it again.');
      this.buffers.set(t.file_path,await this.context.decodeAudioData(await res.arrayBuffer()));
    }
    this.duration=Math.max(0,...project.tracks.map(t=>this.buffers.get(t.file_path)?.duration||0));
  }
  stop() {this.offset=this.time();this.sources.forEach(s=>{try{s.stop();}catch{/* Already ended. */}});this.sources=[];this.playing=false;}
  time() {return this.playing?Math.max(0,Math.min(this.duration,this.offset+(this.context!.currentTime-this.startTime))):this.offset;}
  async play(project:Project) {
    await this.prepare(project);await this.context!.resume();
    if(this.offset>=this.duration)this.offset=0;
    const solo=project.tracks.some(t=>t.solo);const when=this.context!.currentTime+.03;
    this.startTime=when;this.playing=true;
    for(const t of project.tracks){if(t.mute||(solo&&!t.solo))continue;
      const source=this.context!.createBufferSource();source.buffer=this.buffers.get(t.file_path)!;
      if(this.offset>=source.buffer.duration)continue;
      const gain=this.context!.createGain();gain.gain.value=10**(t.gain_db/20)*(t.phase_invert?-1:1);
      const splitter=this.context!.createChannelSplitter(2);const merger=this.context!.createChannelMerger(2);
      const left=this.context!.createGain(),right=this.context!.createGain();
      left.gain.value=Math.cos((t.pan+1)*Math.PI/4);right.gain.value=Math.sin((t.pan+1)*Math.PI/4);
      const meter=this.context!.createAnalyser();meter.fftSize=512;this.meters.set(t.track_id,{node:meter,data:new Float32Array(512)});
      source.connect(gain).connect(meter).connect(splitter);splitter.connect(left,0);splitter.connect(right,1);
      left.connect(merger,0,0);right.connect(merger,0,1);merger.connect(this.context!.destination);
      source.start(when,this.offset);this.sources.push(source);
    }
  }
  levels():Record<string,number>{const levels:Record<string,number>={};for(const [id,m] of this.meters){m.node.getFloatTimeDomainData(m.data);let sum=0;for(const v of m.data)sum+=v*v;levels[id]=this.playing?Math.min(1,Math.sqrt(sum/m.data.length)*3):0;}return levels;}
  seek(seconds:number){this.stop();this.offset=Math.max(0,Math.min(this.duration,seconds));}
}
export function wavBlob(samples:Float32Array):Blob {
  const buffer=new ArrayBuffer(44+samples.length*8);const v=new DataView(buffer);
  function text(p:number,s:string){for(let i=0;i<s.length;i++)v.setUint8(p+i,s.charCodeAt(i));}
  text(0,'RIFF');v.setUint32(4,buffer.byteLength-8,true);text(8,'WAVE');text(12,'fmt ');
  v.setUint32(16,16,true);v.setUint16(20,3,true);v.setUint16(22,2,true);v.setUint32(24,48000,true);
  v.setUint32(28,384000,true);v.setUint16(32,8,true);v.setUint16(34,32,true);text(36,'data');v.setUint32(40,samples.length*8,true);
  samples.forEach((x,i)=>{v.setFloat32(44+i*8,x,true);v.setFloat32(48+i*8,x,true);});
  return new Blob([buffer],{type:'audio/wav'});
}
