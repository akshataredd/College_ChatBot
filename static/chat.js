const chatBox = document.getElementById('chat')
const input = document.getElementById('input')
const sendBtn = document.getElementById('send')
const voiceBtn = document.getElementById('voice')

function appendMessage(who, text){
  const el = document.createElement('div')
  el.className = 'msg ' + who
  el.textContent = text
  chatBox.appendChild(el)
  chatBox.scrollTop = chatBox.scrollHeight
}

async function send(){
  const text = input.value.trim()
  if(!text) return
  appendMessage('user', text)
  input.value = ''
  const res = await fetch('/api/chat', {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({message:text})})
  if(!res.ok){ appendMessage('bot', 'Error contacting server'); return }
  const j = await res.json()
  appendMessage('bot', j.reply)
  // request server-side TTS for the bot reply and play it
  try{
    const ttsRes = await fetch('/api/tts', {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({text: j.reply})})
    if(ttsRes.ok){
      const blob = await ttsRes.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audio.play().catch(e=>console.warn('TTS play failed', e))
    }
  }catch(e){ console.warn('TTS request failed', e) }
}

sendBtn.addEventListener('click', send)
input.addEventListener('keydown', (e)=>{ if(e.key === 'Enter') send() })

// Basic voice input using Web Speech API
if('webkitSpeechRecognition' in window || 'SpeechRecognition' in window){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  const recog = new SR()
  recog.lang = 'en-US'
  recog.interimResults = false
  voiceBtn.addEventListener('click', ()=>{ recog.start() })
  recog.onresult = (ev)=>{
    const text = ev.results[0][0].transcript
    input.value = text
    send()
  }
  recog.onerror = (ev)=>{ appendMessage('bot', 'Voice input error: '+ev.error) }
} else {
  voiceBtn.disabled = true
}
