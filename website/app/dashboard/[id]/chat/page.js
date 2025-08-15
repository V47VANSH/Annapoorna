"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { Sparkles, RefreshCcw, ImageIcon, Mic, Square } from "lucide-react";
import ReactMarkdown from "react-markdown";
import ChatSidebar from "@/components/ChatSideBar";
import { apiFetch, apiPostJson, apiUrl } from "@/lib/api";

const GREETING = { type: "bot", text: "Hi, Annapoorna here! How may I help you?" };

export default function AnnapoornaChatbot() {
  const { id } = useParams();

  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [imagePreview, setImagePreview] = useState(null);
  const [context, setContext] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isTranscribingAudio, setIsTranscribingAudio] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  const chatContainerRef = useRef(null);

  useEffect(() => {
    if (!id) return;

    (async () => {
      try {
        const data = await apiFetch(`/allChats/${id}`);
        if (Array.isArray(data)) {
          setChats(data);
          if (data.length > 0) setActiveChatId(data[0]._id);
        }
      } catch (err) {
        console.error("Failed to fetch chats:", err);
      }
    })();
  }, [id]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const changeChat = useCallback(
    async (chatId) => {
      const chat = chats.find((c) => String(c._id) === String(chatId));
      if (!chat) {
        console.warn("Chat not found for ID:", chatId);
        return;
      }

      setMessages(chat.messages ?? []);
      setContext(chat.context ?? "");
      setActiveChatId(chatId);

      try {
        await apiPostJson("/setContext", { context: chat.context ?? "", user_id: id });
      } catch (err) {
        setError(err.message || "Could not restore that conversation's context.");
      }
    },
    [chats, id]
  );

  async function generateResponse(userInput) {
    const data = await apiPostJson("/chat", {
      message: userInput || "Explain",
      user_id: id,
    });
    return data.response;
  }

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    setMessages((prev) => [...prev, { type: "user", text: trimmed }]);
    setInput("");
    setError("");
    setIsSending(true);

    try {
      const reply = await generateResponse(trimmed);
      setMessages((prev) => [...prev, { type: "bot", text: reply }]);
    } catch (err) {
      setError(err.message || "Something went wrong.");
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleNewChat = async () => {
    setError("");

    // save the current chat first
    if (id && messages.length > 1) {
      try {
        await apiPostJson("/reset", { user_id: id, messages, context });
      } catch (err) {
        console.error("Failed to save chat:", err);
      }
    }

    setMessages([GREETING]);
    setImagePreview(null);
    setInput("");

    if (!id) return;
    try {
      const data = await apiFetch(`/latestReport/${id}`);
      setContext(data?.report ?? "");
    } catch (err) {
      console.error("Error fetching report:", err);
      setContext("");
    }
  };

  const handleImageChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    setImagePreview(previewUrl);
    setMessages((prev) => [
      ...prev,
      { type: "user", text: "Please identify the disease in this leaf.", image: previewUrl },
    ]);
    setIsUploadingImage(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const data = await apiFetch(`/predict?user_id=${encodeURIComponent(id ?? "")}`, {
        method: "POST",
        body: formData,
      });

      const confidence =
        typeof data.confidence === "number"
          ? ` _(confidence: ${Math.round(data.confidence * 100)}%)_`
          : "";

      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: `**Detected: ${data.disease}**${confidence}\n\n${data.response ?? ""}`,
        },
      ]);
    } catch (err) {
      setError(err.message || "Image upload failed.");
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: `Sorry, I could not analyse that image. ${err.message ?? ""}` },
      ]);
    } finally {
      setIsUploadingImage(false);
      setImagePreview(null);
      // so the same file can be picked again
      event.target.value = "";
    }
  };

  const transcribeAudio = async (audioBlob) => {
    setIsTranscribingAudio(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", audioBlob, "recording.webm");

      const response = await fetch(apiUrl("/transcribe"), {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) throw new Error(data.error || "Transcription failed.");
      if (data.transcription) setInput(data.transcription);
    } catch (err) {
      setError(err.message || "Could not transcribe that recording.");
    } finally {
      setIsTranscribingAudio(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = () => {
        // MediaRecorder records webm/ogg, not wav
        const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
        transcribeAudio(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      setError("Could not access the microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="flex">
      <ChatSidebar chats={chats} activeChatId={activeChatId} onSelectChat={changeChat} />

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
              <div
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto mb-4 pr-2 space-y-3"
              >
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`rounded-xl px-4 py-2 max-w-[80%] break-words text-sm w-fit ${
                      msg.type === "user"
                        ? "ml-auto bg-green-200 text-right"
                        : "bg-green-50 text-left"
                    }`}
                    style={{ wordBreak: "break-word", overflowWrap: "break-word" }}
                  >
                    {msg.image && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={msg.image}
                        alt="Uploaded leaf"
                        className="mb-2 max-w-full rounded-lg"
                      />
                    )}
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                ))}
                {isSending && (
                  <div className="bg-green-50 rounded-xl px-4 py-2 text-sm w-fit animate-pulse">
                    Annapoorna is typing...
                  </div>
                )}
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
                  className={`cursor-pointer ${
                    isRecording
                      ? "text-red-600 animate-pulse"
                      : "text-green-700 hover:text-green-900"
                  }`}
                  title={isRecording ? "Stop recording" : "Start voice recording"}
                >
                  {isRecording ? (
                    <Square className="w-6 h-6" />
                  ) : (
                    <Mic className="w-6 h-6" />
                  )}
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
                  disabled={isSending}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white rounded-xl"
                >
                  Send
                </button>
              </div>

              {error && (
                <div role="alert" className="mt-2 text-sm text-red-600">
                  {error}
                </div>
              )}
              {imagePreview && (
                <div className="mt-2 text-sm text-green-800">Image ready ✅</div>
              )}
              {isUploadingImage && (
                <div className="mt-2 text-sm text-blue-600 animate-pulse">
                  🖼️ Analysing image...
                </div>
              )}
              {isRecording && (
                <div className="mt-2 text-sm text-red-600 animate-pulse">
                  🔴 Recording... Click stop when done
                </div>
              )}
              {isTranscribingAudio && (
                <div className="mt-2 text-sm text-yellow-600 animate-pulse">
                  🎤 Transcribing audio...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
