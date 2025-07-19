"use client"
import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { Sparkles, RefreshCcw, ImageIcon, Mic, Square } from "lucide-react";
import ChatSidebar from "@/components/ChatSideBar";
export default function AnnapoornaChatbot() {
const dummyChats = [
  { id: "1", name: "Customer Support" },
  { id: "2", name: "Project Ideas" },
  { id: "3", name: "NeuroVox Logs" },
];
const handleChatClick = (chatId) => {
    console.log("Chat clicked:", chatId);
    // You can load messages or redirect here
  };

const [activeChatId, setActiveChatId] = useState("1"); // Default or selected chat

  const params=useParams();
  const id=params.id;
  const [messages, setMessages] = useState([
    { type: "bot", text: "Hi, Annapoorna here! How may I help you?" },
  ]);
  const [input, setInput] = useState("");
  const [imagePreview, setImagePreview] = useState(null);
  const [context, setContext]=useState("context");
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const chatContainerRef = useRef(null);
  
  const handleSend = async () => {
    if (!input.trim() && !imagePreview) return;

    const userMessage = { type: "user", text: input.trim(), image: imagePreview };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setImagePreview(null);

    const botReply = await generateResponse(input.trim());
    const botMessage = { type: "bot", text: botReply };
    setMessages((prev) => [...prev, botMessage]);
  };

  const handleNewChat = () => {
    setMessages([
      { type: "bot", text: "Hi, Annapoorna here! How may I help you?" },
    ]);
    setImagePreview(null);
    setInput("");
    clearChat();
  };

  const handleImageChange = async (e) => {
  const file = e.target.files[0];
  if (file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/predict", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      console.log("Prediction:", data);
      setImagePreview(URL.createObjectURL(file)); // Optional preview
      setPrediction(data); // You can store and display this
    } catch (err) {
      console.error("Upload failed", err);
    }
  }
};


  async function generateResponse(userInput) {
  try {
    const input = userInput || "Explain";
    const response = await fetch(`http://localhost:8000/chat/${encodeURIComponent(input)}`, {
      method: "POST"
    });
    const data = await response.json();
    return data.response; // this should be the bot's reply
  } catch (error) {
    console.error("Error:", error);
    return "Sorry, something went wrong.";
  }
}

async function clearChat() {
  try {
    const response = await fetch("http://localhost:8000/reset", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: id,
        messages: messages,
        context: context,
      }),
    });

    const data = await response.json();
    return data.message;
  } catch (error) {
    console.error("Error:", error);
    return "Sorry, something went wrong.";
  }
}


  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        setAudioBlob(blob);
        transcribeAudio(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Error accessing microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');

      const response = await fetch('http://localhost:8000/transcribe', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.transcription) {
        setInput(data.transcription);
      }
    } catch (error) {
      console.error('Transcription error:', error);
    }
  };

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex">
     <div className="flex">
      <ChatSidebar chats={dummyChats} onChatClick={handleChatClick} />
    </div>
    <div className="w-full min-h-screen bg-gradient-to-br from-green-100 via-yellow-50 to-green-200 flex flex-col items-center p-6">
      <div className="max-w-2xl w-full">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-green-800 flex items-center gap-2">
            <Sparkles className="text-yellow-500 w-6 h-6" /> Annapoorna
          </h1>
          <button
            onClick={handleNewChat}
            className="flex items-center gap-1 px-3 py-1 border border-green-600 text-green-700 rounded-xl text-sm hover:bg-green-100"
          >
            <RefreshCcw className="w-4 h-4" /> New Chat
          </button>
        </div>

        <div className="rounded-2xl shadow-xl border border-green-300 bg-white/80 backdrop-blur-md">
          <div className="p-4 h-[500px] overflow-hidden flex flex-col">
            <div ref={chatContainerRef} className="flex-1 overflow-y-auto mb-4 pr-2 space-y-3">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`rounded-xl px-4 py-2 max-w-[80%] break-words text-sm w-fit ${
                    msg.type === "user"
                      ? "ml-auto bg-green-200 text-right"
                      : "bg-green-50 text-left"
                  }`}
                  style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}
                >
                  {msg.image && <img src={msg.image} alt="uploaded" className="mb-2 max-w-full rounded-lg" />}
                  {msg.text}
                </div>
              ))}
            </div>
            <div className="flex gap-2 items-center">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
                id="image-upload"
              />
              <label
                htmlFor="image-upload"
                className="cursor-pointer text-green-700 hover:text-green-900"
                title="Upload image"
              >
                <ImageIcon className="w-6 h-6" />
              </label>
              
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`cursor-pointer ${isRecording ? 'text-red-600 animate-pulse' : 'text-green-700 hover:text-green-900'}`}
                title={isRecording ? "Stop recording" : "Start voice recording"}
              >
                {isRecording ? <Square className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
              </button>

              <input
                type="text"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                className="flex-1 p-2 border border-green-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <button
                onClick={handleSend}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl"
              >
                Send
              </button>
            </div>
            {imagePreview && (
              <div className="mt-2 text-sm text-green-800">Image ready to send ✅</div>
            )}
            {isRecording && (
              <div className="mt-2 text-sm text-red-600 animate-pulse">🔴 Recording... Click stop when done</div>
            )}
          </div>
        </div>
      </div>
    </div>
    </div>
  );
}
