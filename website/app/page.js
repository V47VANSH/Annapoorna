"use client";
import { useState } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [user, setUser] = useState({ name: "", address: "", email: "", phone: "" });
  const [isLogin, setIsLogin] = useState(false);
  const router = useRouter();

  const handleRegister = async () => {
  if (!user.address) return alert("Please provide an address!");

  const apiKey = "REDACTED-GEOCODE-KEY";
  const url = `https://geocode.maps.co/search?q=${encodeURIComponent(user.address)}&api_key=${apiKey}`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Geocoding failed.");
    const data = await response.json();

    if (!data || !data[0] || !data[0].boundingbox) {
      return alert("Address not found or invalid.");
    }

    const boundingBox = data[0].boundingbox.map(coord => parseFloat(coord)); // Convert to numbers

    const res = await axios.post("http://localhost:8000/register", {
      ...user,
      location: boundingBox, // 👈 send bounding box
    });

    if (res.data.id) {
      router.push(`/dashboard/${res.data.id}/home`);
    } else {
      alert(res.data.error || "Registration failed.");
    }
  } catch (err) {
    console.error("Registration Error:", err);
    alert(err.response?.data?.error || "Registration failed.");
  }
};


  const handleLogin = async () => {
    try {
      const res = await axios.post("http://localhost:8000/login", {
        email: user.email,
      });
      if (res.data.id) {
        router.push(`/dashboard/${res.data.id}/home`);
      } else {
        alert(res.data.error);
      }
    } catch (err) {
      alert(err.response?.data?.error || "Login failed.");
    }
  };


  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-gray-100">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4 text-center">{isLogin ? "Login" : "Register"}</h1>

        {!isLogin && (
          <>
            <input
              type="text"
              placeholder="Name"
              className="input"
              onChange={(e) => setUser({ ...user, name: e.target.value })}
            />
            <input
              type="text"
              placeholder="Phone"
              className="input"
              onChange={(e) => setUser({ ...user, phone: e.target.value })}
            />
            <input
              type="text"
              placeholder="Address"
              className="input"
              onChange={(e) => setUser({ ...user, address: e.target.value })}
            />
          </>
        )}

        <input
          type="email"
          placeholder="Email"
          className="input mt-4"
          onChange={(e) => setUser({ ...user, email: e.target.value })}
        />

        <button
          className="w-full bg-blue-600 text-white py-2 rounded mt-4 hover:bg-blue-700"
          onClick={isLogin ? handleLogin : handleRegister}
        >
          {isLogin ? "Login" : "Register"}
        </button>

        <p
          className="text-blue-600 text-sm text-center mt-3 cursor-pointer"
          onClick={() => setIsLogin(!isLogin)}
        >
          {isLogin ? "New here? Register" : "Already a user? Login"}
        </p>
      </div>

      <style jsx>{`
        .input {
          width: 100%;
          padding: 10px;
          margin-bottom: 12px;
          border: 1px solid #ccc;
          border-radius: 6px;
        }
      `}</style>
    </div>
  );
}
