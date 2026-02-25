"use client";

import { useLectureStore } from "@/store/useLectureStore";
import MiniTimetable from "./MiniTimetable";
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import TimetableView from "./TimetableView";
import OptimizationDetails from "./OptimizationDetails";
import { Battery } from "lucide-react";

export default function TimetableCardsRow() {
    const { optimizationResult } = useLectureStore();
    const [selectedSchedule, setSelectedSchedule] = useState<any | null>(null);

    if (!optimizationResult || !optimizationResult.top_schedules || optimizationResult.top_schedules.length === 0) {
        return null;
    }

    const alternativeSchedules = optimizationResult.top_schedules.slice(1);

    if (alternativeSchedules.length === 0) return null;

    return (
        <div className="w-full flex flex-col bg-white rounded-xl shadow-sm border p-4">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                Alternative Quantum Optimized Schedules
                <span className="text-sm font-normal text-muted-foreground ml-2">(Click card to expand)</span>
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-4 pb-2">
                {alternativeSchedules.map((res: any, idx: number) => (
                    <div
                        key={idx}
                        className="bg-white border-2 rounded-xl p-3 cursor-pointer hover:shadow-lg transition-all hover:border-primary group flex flex-col hover:-translate-y-1"
                        onClick={() => setSelectedSchedule(res)}
                    >
                        <div className="flex justify-between items-center mb-3">
                            <span className="font-bold text-sm text-primary-foreground bg-primary px-2.5 py-0.5 rounded-full shadow-sm">
                                Rank #{idx + 2}
                            </span>
                            <span className="text-[10px] font-semibold text-primary/0 group-hover:text-primary transition-all">
                                VIEW
                            </span>
                        </div>

                        <div className="flex-1 mb-4 border rounded p-1 bg-gray-50/50">
                            <MiniTimetable schedule={res.schedule} />
                        </div>

                        <div className="pt-3 border-t flex justify-between items-center text-sm">
                            <div className="flex items-center gap-1.5 text-muted-foreground font-medium text-xs">
                                <Battery className="w-4 h-4" />
                                Energy
                            </div>
                            <span className={`font-bold tabular-nums ${res.energy < 0 ? 'text-green-600' : 'text-red-500'}`}>
                                {typeof res.energy === 'number' ? res.energy.toFixed(2) : res.energy}
                            </span>
                        </div>
                    </div>
                ))}
            </div>

            <Dialog open={!!selectedSchedule} onOpenChange={(open) => !open && setSelectedSchedule(null)}>
                <DialogContent className="max-w-[95vw] lg:max-w-[1200px] w-full h-[90vh] flex flex-col p-6 gap-0">
                    <DialogHeader className="mb-4 shrink-0">
                        <DialogTitle className="text-2xl font-bold flex items-center gap-3">
                            Detailed Schedule View
                            <span className="text-sm font-medium bg-primary/10 text-primary px-3 py-1 rounded-full">
                                Energy: {typeof selectedSchedule?.energy === 'number' ? selectedSchedule.energy.toFixed(2) : selectedSchedule?.energy}
                            </span>
                        </DialogTitle>
                        <DialogDescription>
                            Review the exact timetable layout and the quantum evaluation metrics below.
                        </DialogDescription>
                    </DialogHeader>

                    {selectedSchedule && (
                        <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-6 overflow-hidden">
                            {/* Left: Timetable */}
                            <div className="flex-1 h-full min-h-0">
                                <TimetableView schedule={selectedSchedule.schedule} />
                            </div>

                            {/* Right: Details Panel */}
                            <div className="w-full lg:w-[450px] shrink-0 overflow-y-auto pr-2">
                                <OptimizationDetails result={selectedSchedule} />
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
