import { useEffect, useRef, useState } from 'react';
import { sendChat } from '../api';
import { getUserPosition } from './LeafletMap';

export const NARA_COMMANDS = [
  ['/cari','Cari Rumah Sakit','Cari RS di '], ['/terdekat','RS Terdekat','RS terdekat'],
  ['/layanan','Layanan Medis','Cari RS dengan layanan '], ['/fasilitas','Fasilitas','Cari RS dengan fasilitas '],
  ['/bandingkan','Bandingkan RS','Bandingkan '], ['/jadwal','Jam Operasional','Jam operasional '],
  ['/kontak','Kontak','Nomor telepon '], ['/igd','Cari IGD','Cari IGD'], ['/bantuan','Bantuan','Bantuan'],
];

export default function useNaraConversation(toast) {
  const [open,setOpen]=useState(false), [expanded,setExpanded]=useState(false);
  const [messages,setMessages]=useState([]), [state,setState]=useState(null);
  const [input,setInput]=useState(''), [loading,setLoading]=useState(false);
  const [location,setLocation]=useState(null), [locating,setLocating]=useState(false);
  const [history,setHistory]=useState([]), [historyOpen,setHistoryOpen]=useState(false);
  const [comparison,setComparison]=useState([]), [paletteIndex,setPaletteIndex]=useState(0), [paletteClosed,setPaletteClosed]=useState(false);
  const inputRef=useRef(null),bottomRef=useRef(null),scrollRef=useRef(null),nearBottom=useRef(true);
  const sendingRef=useRef(false),requestRef=useRef(null),idRef=useRef(crypto.randomUUID());
  const commands=!paletteClosed && input.startsWith('/') ? NARA_COMMANDS.filter(c=>c[0].startsWith(input.split(' ')[0])):[];
  const minimizeChat=()=>setOpen(false), closeChat=minimizeChat;
  useEffect(()=>{const show=()=>setOpen(true);window.addEventListener('carisehat:open-chat',show);return()=>{window.removeEventListener('carisehat:open-chat',show);requestRef.current?.abort();};},[]);
  useEffect(()=>{if(open)inputRef.current?.focus();},[open]);
  useEffect(()=>{if(open && nearBottom.current && scrollRef.current)scrollRef.current.scrollTop=scrollRef.current.scrollHeight;},[messages,loading,open]);
  useEffect(()=>{if(inputRef.current){inputRef.current.style.height='auto';inputRef.current.style.height=`${Math.min(inputRef.current.scrollHeight,130)}px`;}},[input]);
  const chooseCommand=c=>{setInput(c[2]);setPaletteClosed(true);setPaletteIndex(0);inputRef.current?.focus();};
  const changeInput=value=>{setInput(value);setPaletteClosed(false);setPaletteIndex(0);};
  const send=async(raw,position=location)=>{
    const text=String(raw||'').trim();if(!text||text.length>4000||sendingRef.current)return;
    const command=NARA_COMMANDS.find(c=>c[0]===text);if(command){chooseCommand(command);return;}
    sendingRef.current=true;setLoading(true);setInput('');nearBottom.current=true;
    setMessages(old=>[...old,{id:crypto.randomUUID(),role:'user',text}]);
    const controller=new AbortController();requestRef.current=controller;
    const timer=window.setTimeout(()=>controller.abort(),30000);
    try{
      const response=await sendChat({text,state:state||undefined,lat:position?.[0],lon:position?.[1],location_status:position?'granted':'unknown'},controller.signal);
      setState(response.state||null);
      setMessages(old=>[...old,{...response,id:crypto.randomUUID(),role:'assistant',quickReplies:response.quick_replies||[],emergency:Boolean(response.is_emergency),retry:response.retryable?text:null}]);
    }catch{
      setMessages(old=>[...old,{id:crypto.randomUUID(),role:'assistant',text:'NARA belum dapat dihubungi. Coba kembali.',kind:'error',retry:text}]);
    }finally{window.clearTimeout(timer);requestRef.current=null;sendingRef.current=false;setLoading(false);}
  };
  const enableLocation=async()=>{if(locating||loading)return;setLocating(true);try{const p=await getUserPosition();setLocation(p);if(state?.pending==='location')send('Yang paling dekat saja',p);else toast('Lokasi aktif untuk mencari jarak garis lurus.','success');}catch{toast('Lokasi tidak tersedia. Ketik wilayah, misalnya “Ganti ke Medan”.','info');}finally{setLocating(false);}};
  const saved=()=>({id:idRef.current,title:messages.find(m=>m.role==='user')?.text.slice(0,45)||'Percakapan baru',messages,state});
  const reset=()=>{idRef.current=crypto.randomUUID();setMessages([]);setState(null);setInput('');setLocation(null);setComparison([]);};
  const newConversation=()=>{if(loading)return;const snapshot=saved();if(messages.length)setHistory(old=>[snapshot,...old.filter(s=>s.id!==snapshot.id)].slice(0,20));reset();};
  const selectHistory=s=>{if(loading)return;const current=saved();setHistory(old=>[...(messages.length?[current]:[]),...old.filter(x=>x.id!==s.id&&x.id!==current.id)].slice(0,20));idRef.current=s.id;setMessages(s.messages);setState(s.state);setInput('');setLocation(null);setComparison([]);setHistoryOpen(false);};
  const deleteConversation=id=>{if(loading||!window.confirm('Hapus percakapan ini?'))return;if(!id)reset();else setHistory(old=>old.filter(s=>s.id!==id));};
  const toggleComparison=h=>setComparison(old=>old.some(x=>x.id===h.id)?old.filter(x=>x.id!==h.id):[...old,h].slice(-3));
  const onInputKey=e=>{if(e.nativeEvent.isComposing)return;if(commands.length&&['ArrowUp','ArrowDown','Enter','Tab','Escape'].includes(e.key)){e.preventDefault();e.stopPropagation();if(e.key==='Escape')setPaletteClosed(true);else if(e.key==='ArrowDown')setPaletteIndex(i=>(i+1)%commands.length);else if(e.key==='ArrowUp')setPaletteIndex(i=>(i+commands.length-1)%commands.length);else chooseCommand(commands[paletteIndex]);}else if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(input);}};
  return {open,setOpen,expanded,setExpanded,messages,input,changeInput,loading,state,location,locating,bottomRef,inputRef,scrollRef,nearBottom,send,enableLocation,minimizeChat,closeChat,history,historyOpen,setHistoryOpen,newConversation,selectHistory,deleteConversation,comparison,toggleComparison,commands,paletteIndex,chooseCommand,onInputKey};
}
