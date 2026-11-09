// # SPEC-004
import { create } from 'zustand';
export const effects = ['HARD_MUTE','NASA_WALKIE_TALKIE','UNDERWATER_WOMB','ANALOG_TAPE_STOP','TAPE_STUTTER_DEGRADE','SUB_40HZ_DROP'] as const;
export type Effect = typeof effects[number];
export type Region = {region_id:string;start_sec:number;end_sec:number;effect_type:Effect;wet_mix:number;fade_ms:number};
export type Track = {track_id:string;name:string;file_path:string;gain_db:number;pan:number;mute:boolean;solo:boolean;phase_invert:boolean;channel_strip:Record<string,number>;regions:Region[]};
export type Master = {mono_bass_cutoff_hz:85;stereo_width:number;pultec_low_boost_db:number;mud_cut_db:number;mid_bite_db:number;air_boost_db:number;parallel_comp_mix:number;tape_drive:number;target_lufs:number;ceiling_db:-.3;regions:Region[]};
export type Project = {project_id:string;sample_rate:48000;master_bus:Master;tracks:Track[];bpm?:number|null};
export const initialProject = ():Project => ({project_id:'',sample_rate:48000,master_bus:{mono_bass_cutoff_hz:85,stereo_width:1.15,pultec_low_boost_db:2.2,mud_cut_db:-2.5,mid_bite_db:1.8,air_boost_db:1.6,parallel_comp_mix:.18,tape_drive:1.22,target_lufs:-9.5,ceiling_db:-.3,regions:[]},tracks:[]});
interface State {project:Project;past:Project[];future:Project[];transaction:Project|null;
  edit:(fn:(p:Project)=>void)=>void;load:(p:Project)=>void;undo:()=>void;redo:()=>void;
  begin:()=>void;commit:()=>void;save:()=>void;restore:()=>void;}
export const store = create<State>((set,get)=>({project:initialProject(),past:[],future:[],transaction:null,
  edit: fn => {const s=get();const next=structuredClone(s.project);fn(next);
    set({project:next,past:s.transaction?s.past:[...s.past,s.project].slice(-100),future:[]});get().save();},
  load:p=>{set({project:structuredClone(p),past:[],future:[],transaction:null});get().save();},
  begin:()=>set({transaction:structuredClone(get().project)}),
  commit:()=>{const s=get();if(s.transaction)set({past:[...s.past,s.transaction].slice(-100),transaction:null});},
  undo:()=>{const s=get();if(!s.past.length)return;set({project:s.past.at(-1)!,past:s.past.slice(0,-1),future:[s.project,...s.future]});get().save();},
  redo:()=>{const s=get();if(!s.future.length)return;set({project:s.future[0],past:[...s.past,s.project],future:s.future.slice(1)});get().save();},
  save:()=>localStorage.setItem('k1-project',JSON.stringify(get().project)),
  restore:()=>{try{const p=JSON.parse(localStorage.getItem('k1-project')||'null') as Project|null;
    if(p&&p.sample_rate===48000&&Array.isArray(p.tracks)&&p.master_bus)set({project:p,past:[],future:[]});}catch{/* An invalid local cache is not executable data. */}}
}));
