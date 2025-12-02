import React, { useState } from "react";

export default function TripForm({ onSubmit }) {
  const [currentLocation, setCurrentLocation] = useState("");
  const [pickupLocation, setPickupLocation] = useState("");
  const [dropoffLocation, setDropoffLocation] = useState("");
  const [cycleUsed, setCycleUsed] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit({
        currentLocation,
        pickupLocation,
        dropoffLocation,
        cycleUsed: Number(cycleUsed),
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <form className="bg-white p-6 rounded shadow-md space-y-4" onSubmit={handleSubmit}>
        <h2 className="text-xl font-bold">Plan Your Trip</h2>

        <input
          type="text"
          placeholder="Current Location"
          value={currentLocation}
          onChange={(e) => setCurrentLocation(e.target.value)}
          className="border p-2 rounded w-full"
          required
        />

        <input
          type="text"
          placeholder="Pickup Location"
          value={pickupLocation}
          onChange={(e) => setPickupLocation(e.target.value)}
          className="border p-2 rounded w-full"
          required
        />

        <input
          type="text"
          placeholder="Dropoff Location"
          value={dropoffLocation}
          onChange={(e) => setDropoffLocation(e.target.value)}
          className="border p-2 rounded w-full"
          required
        />

        <input
          type="number"
          placeholder="Current Cycle Used (Hrs)"
          value={cycleUsed}
          onChange={(e) => setCycleUsed(e.target.value)}
          className="border p-2 rounded w-full"
          min={0}
          required
        />

        <button
          type="submit"
          disabled={loading}
          className={`px-4 py-2 rounded text-white w-full ${
            loading ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "Processing..." : "Submit"}
        </button>
      </form>

      {loading && (
        <div
          className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50"
          role="alert"
          aria-busy="true"
        >
          <div className="bg-white p-6 rounded shadow-md w-80 text-center">
            <h3 className="text-lg font-bold mb-2">Please be patient</h3>
            <p className="mb-4 text-sm">
              Calculating your route may take a few seconds for long trips.
            </p>
            <div className="flex justify-center">
              <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
