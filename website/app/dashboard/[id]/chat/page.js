"use client"
import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { Sparkles, RefreshCcw, ImageIcon } from "lucide-react";

export default function AnnapoornaChatbot() {
  const params=useParams();
  const id=params.id;
  const [messages, setMessages] = useState([
    { type: "bot", text: "Hi, Annapoorna here! How may I help you?" },
  ]);
  const [input, setInput] = useState("");
  const [imagePreview, setImagePreview] = useState(null);
  const [context, setContext]=useState("context");
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

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  async function generateResponse(userInput) {
  try {
    const response = await fetch(`http://localhost:8000/chat/${encodeURIComponent(userInput)}`, {
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


  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-100 via-yellow-50 to-green-200 flex flex-col items-center p-6">
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
          </div>
        </div>
      </div>
    </div>
  );
}
