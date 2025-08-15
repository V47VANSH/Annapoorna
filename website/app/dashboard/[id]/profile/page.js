"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

export default function ProfilePage() {
  const { id } = useParams();
  const [userData, setUserData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    (async () => {
      try {
        setUserData(await apiFetch(`/profile/${id}`));
      } catch (err) {
        console.error("Error fetching user data:", err);
        setError(err.message || "Failed to load user profile");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) {
    return (
      <div className="text-center text-green-700 font-semibold mt-10">
        Loading profile...
      </div>
    );
  }

  if (error || !userData) {
    return (
      <div role="alert" className="text-center text-red-600 font-semibold mt-10">
        {error || "Failed to load user profile"}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-100 via-green-200 to-green-300 p-6 flex justify-center items-center">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-xl w-full border border-green-200">
        <h1 className="text-3xl font-bold text-green-700 mb-4 text-center">
          🌱 Farmer Profile
        </h1>
        <div className="space-y-4">
          <p>
            <span className="font-semibold text-green-800">👤 Name:</span>{" "}
            {userData.name}
          </p>
          <p>
            <span className="font-semibold text-green-800">📬 Address:</span>{" "}
            {userData.address}
          </p>
          <p>
            <span className="font-semibold text-green-800">📧 Email:</span>{" "}
            {userData.email}
          </p>
          <p>
            <span className="font-semibold text-green-800">📞 Phone:</span>{" "}
            {userData.phone}
          </p>
          <p>
            <span className="font-semibold text-green-800">
              📍 Location Bounding Box:
            </span>
            <br />
            <code className="text-sm text-green-600">
              [{userData.bounding_box?.join(", ")}]
            </code>
          </p>
        </div>
      </div>
    </div>
  );
}
