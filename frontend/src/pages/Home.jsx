import React, { useState } from "react";
import TripForm from "../components/TripForm";
import TripLogs from "../components/TripLogs";
import { generateELDLogs } from "../utils/generateELDLogs";

export default function Home() {
  const [data, setData] = useState(null);

  const handleSubmit = async (formData) => {
    setData(null);
    try {
      // const res = await fetch("http://127.0.0.1:8000/api/trip-plan/", {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify(formData),
      // });
      // Use environment variable for API URL, fallback to localhost
      const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      
      console.log("Sending formData:", formData);
      const res = await fetch(`${API_URL}/api/trip-plan/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          cycleUsed: Number(formData.cycleUsed)  // ensure it's a number
        }),
      });

      const json = await res.json();

      if (json.error) {
        alert(json.error);
        return;
      }

      // Use backend ELD logs directly
      setData({
        ...json,
        eldLogs: json.eldLogs,
      });
    } catch (err) {
      console.error(err);
      alert("Error fetching trip plan");
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <TripForm onSubmit={handleSubmit} />
      {data && <TripLogs {...data} />}
    </div>
  );
}
