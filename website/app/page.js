"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, apiPostJson } from "@/lib/api";

const EMPTY_USER = { name: "", address: "", email: "", phone: "" };

export default function LoginPage() {
  const [user, setUser] = useState(EMPTY_USER);
  const [isLogin, setIsLogin] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const update = (field) => (event) =>
    setUser((prev) => ({ ...prev, [field]: event.target.value }));

  const handleRegister = async () => {
    if (!user.name.trim()) return setError("Please enter your name.");
    if (!user.email.trim()) return setError("Please enter your email.");
    if (!user.address.trim()) return setError("Please provide an address.");

    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const geoResponse = await fetch(
        `/api/geocode?address=${encodeURIComponent(user.address)}`
      );
      const geo = await geoResponse.json();
      if (!geoResponse.ok) {
        throw new Error(geo.error || "Could not locate that address.");
      }

      const data = await apiPostJson("/register", {
        ...user,
        location: geo.boundingBox,
      });

      if (data.error) throw new Error(data.error);
      if (!data.id) throw new Error("Registration failed.");

      router.push(`/dashboard/${data.id}/home`);
    } catch (err) {
      setError(err.message || "Registration failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogin = async () => {
    if (!user.email.trim()) return setError("Please enter your email.");

    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const data = await apiPostJson("/login", { email: user.email });
      if (data.error) throw new Error(data.error);
      if (!data.id) throw new Error("Login failed.");

      router.push(`/dashboard/${data.id}/home`);
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemo = async () => {
    setError("");
    setNotice("Opening the demo farm...");
    setIsSubmitting(true);
    try {
      const data = await apiFetch("/demo");
      if (!data?.id) throw new Error("Demo user is unavailable.");
      router.push(`/dashboard/${data.id}/home`);
    } catch (err) {
      setNotice("");
      setError(
        `${err.message || "Could not open the demo."} ` +
          "Is the backend running on port 8000?"
      );
      setIsSubmitting(false);
    }
  };

  const submit = isLogin ? handleLogin : handleRegister;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-gradient-to-br from-emerald-50 to-amber-50">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md border border-emerald-100">
        <h1 className="text-2xl font-bold mb-1 text-center text-emerald-800">
          🌾 Annapoorna
        </h1>
        <p className="text-center text-sm text-gray-500 mb-5">
          {isLogin ? "Welcome back" : "Create your farmer profile"}
        </p>

        {!isLogin && (
          <>
            <input
              type="text"
              placeholder="Name"
              className="input"
              value={user.name}
              onChange={update("name")}
            />
            <input
              type="tel"
              placeholder="Phone"
              className="input"
              value={user.phone}
              onChange={update("phone")}
            />
            <input
              type="text"
              placeholder="Address (used to locate your field)"
              className="input"
              value={user.address}
              onChange={update("address")}
            />
          </>
        )}

        <input
          type="email"
          placeholder="Email"
          className="input"
          value={user.email}
          onChange={update("email")}
          onKeyDown={(e) => e.key === "Enter" && !isSubmitting && submit()}
        />

        {error && (
          <p role="alert" className="text-red-600 text-sm mt-2">
            {error}
          </p>
        )}
        {notice && <p className="text-emerald-700 text-sm mt-2">{notice}</p>}

        <button
          className="w-full bg-emerald-600 text-white py-2 rounded mt-4 hover:bg-emerald-700 disabled:opacity-60"
          onClick={submit}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Please wait..." : isLogin ? "Login" : "Register"}
        </button>

        <button
          type="button"
          className="w-full text-emerald-700 text-sm text-center mt-3 cursor-pointer hover:underline"
          onClick={() => {
            setIsLogin((prev) => !prev);
            setError("");
            setNotice("");
          }}
        >
          {isLogin ? "New here? Register" : "Already a user? Login"}
        </button>

        <div className="flex items-center gap-3 my-5">
          <span className="h-px flex-1 bg-gray-200" />
          <span className="text-xs uppercase tracking-wide text-gray-400">or</span>
          <span className="h-px flex-1 bg-gray-200" />
        </div>

        <button
          type="button"
          onClick={handleDemo}
          disabled={isSubmitting}
          className="w-full border-2 border-amber-400 text-amber-700 font-medium py-2 rounded hover:bg-amber-50 disabled:opacity-60"
        >
          Skip registration and try the demo farm
        </button>
        <p className="text-xs text-gray-500 mt-2 text-center">
          Opens a seeded field in Ludhiana, Punjab. No account, no API keys
          needed.
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
