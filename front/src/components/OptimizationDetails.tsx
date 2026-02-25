"use client";

import { useLectureStore } from "@/store/useLectureStore";

export default function OptimizationDetails({ result }: { result?: any }) {
    const storeResult = useLectureStore(state => state.optimizationResult);
    const activeResult = result || storeResult;

    if (!activeResult || !activeResult.breakdown) {
        return null;
    }

    const { energy, total_credits, breakdown } = activeResult;

    return (
        <div className="mt-6 border rounded-xl overflow-hidden shadow-sm bg-white">
            <div className="bg-muted px-4 py-3 border-b flex justify-between items-center">
                <h3 className="font-bold text-gray-900">Optimization Result Insights</h3>
                <div className="flex space-x-4 text-sm font-semibold">
                    <span className="text-secondary-foreground text-xs bg-secondary px-2 py-1 rounded">
                        Total Credits: {total_credits}
                    </span>
                    <span className="text-primary-foreground text-xs bg-primary px-2 py-1 rounded">
                        Total Energy: {typeof energy === 'number' ? energy.toFixed(2) : energy}
                    </span>
                </div>
            </div>

            <div className="p-4 bg-gray-50 text-sm">
                <p className="text-muted-foreground mb-4">
                    The quantum numerical value (Energy) is a combination of rewards (negative values) and penalties (positive values).
                    The lower the energy, the better the schedule. Here is why this schedule was chosen:
                </p>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Metrics Cards */}
                    {Object.entries(breakdown).map(([key, value]) => {
                        const val = value as number;
                        const isPenalty = val > 0;
                        const isReward = val < 0;

                        let colorClass = "text-gray-500";
                        if (isPenalty) colorClass = "text-red-500 font-medium";
                        if (isReward) colorClass = "text-green-600 font-bold";

                        const formatName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

                        return (
                            <div key={key} className="bg-white p-3 rounded border flex flex-col justify-between shadow-sm">
                                <span className="text-xs text-muted-foreground font-semibold mb-1 truncate" title={formatName}>
                                    {formatName}
                                </span>
                                <span className={`text-lg tracking-tight ${colorClass}`}>
                                    {val > 0 ? '+' : ''}{typeof val === 'number' ? val.toFixed(2) : val}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
