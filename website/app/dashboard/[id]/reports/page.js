"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { apiFetch } from "@/lib/api";

export default function ReportsPage() {
  const { id } = useParams();
  const [reports, setReports] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    (async () => {
      try {
        const data = await apiFetch(`/allReports/${id}`);
        setReports(data.reports || []);
      } catch (err) {
        console.error("Error fetching reports:", err);
        setError(err.message || "Failed to fetch reports");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  // date can be {$date: ...} (BSON) or a plain string
  const formatDate = (date) => {
    const parsed = new Date(date?.$date ?? date);
    return Number.isNaN(parsed.getTime()) ? "Unknown date" : parsed.toLocaleString();
  };

  if (loading) {
    return <div className="p-6 text-green-700">Loading reports...</div>;
  }

  if (error) {
    return (
      <div role="alert" className="p-6 text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Field Reports</h1>
      {reports.length === 0 ? (
        <p className="text-gray-600">
          No reports yet. Your first report is generated shortly after you log in,
          then daily thereafter.
        </p>
      ) : (
        <ul className="space-y-4">
          {reports.map((report) => (
            <li
              key={report._id?.$oid ?? report._id ?? report.date?.$date ?? report.date}
              className="border p-4 rounded shadow bg-white"
            >
              <p className="text-sm text-gray-500 mb-2">{formatDate(report.date)}</p>
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{report.report || "No status provided."}</ReactMarkdown>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
