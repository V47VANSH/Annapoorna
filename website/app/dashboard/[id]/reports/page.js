"use client";
import ReactMarkdown from 'react-markdown';
import { useEffect, useState } from "react";
import axios from "axios";
import { useParams } from "next/navigation";

export default function ReportsPage() {
  const { id } = useParams(); // ✅ Get dynamic route param
  const [reports, setReports] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return; // Wait until id is available

    const fetchReports = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/allReports/${id}`);
        console.log("Fetched response:", res.data);
        setReports(res.data.reports || []);
      } catch (err) {
        console.error("Error fetching reports:", err);
        setError("Failed to fetch reports");
      }
    };

    fetchReports();
  }, [id]);

  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Reports</h1>
      {reports.length === 0 ? (
        <p>No reports available.</p>
      ) : (
       <ul className="space-y-4">
      {reports.map((report, idx) => (
        <li key={idx} className="border p-4 rounded shadow">
          <p><strong>Date:</strong> {new Date(report.date?.$date || report.date).toLocaleString()}</p>
          <p><strong>Status:</strong></p>
          <ReactMarkdown>{report.report || "No status provided."}</ReactMarkdown> 
        </li>
      ))}
</ul>
      )}
    </div>
  );
}
