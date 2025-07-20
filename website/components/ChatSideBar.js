"use client";
import React from "react";

export default function ChatSidebar({ chats, activeChatId, onSelectChat }) {
  return (
    <div className="w-64 h-screen bg-green-800 text-white shadow-md flex flex-col">
      <div className="p-4 text-xl font-bold border-b border-green-700">
        🗂 Previous Chats
      </div>
      <div className="flex-1 overflow-y-auto space-y-1 p-2">
        {chats.map((chat) => (
          <button
            key={chat._id}
            onClick={() => onSelectChat(chat._id)}
            className={`w-full text-left px-4 py-2 rounded-lg hover:bg-green-700 transition ${
              chat._id === activeChatId ? "bg-green-600 font-semibold" : "bg-green-900"
            }`}
          >
            {chat.name}
          </button>
        ))}
      </div>
    </div>
  );
}
