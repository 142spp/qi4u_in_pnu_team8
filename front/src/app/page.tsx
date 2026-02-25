"use client";

import LectureList from "@/components/LectureList";
import OptimizationPanel from "@/components/OptimizationPanel";
import TimetableView from "@/components/TimetableView";
import OptimizationDetails from "@/components/OptimizationDetails";
import TimetableCardsRow from "@/components/TimetableCardsRow";
import { useLectureStore } from "@/store/useLectureStore";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";

export default function Home() {
  const { lectures, selectedIds, optimizedSchedule, clearSelection, optimizationResult } = useLectureStore();

  const selectedLectures = lectures.filter((l) => selectedIds.includes(l.id));

  const hasOptimizationRuns = !!optimizationResult?.top_schedules?.length;

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-[1600px] mx-auto space-y-6">

        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">
              Antigravity Timetable Optimizer <span className="text-sm font-medium text-primary bg-primary/10 px-2 py-1 rounded ml-2">Quantum Prototype</span>
            </h1>
            <p className="text-muted-foreground mt-1">Search lectures, add to list, and run Quantum Annealing to resolve conflicts.</p>
          </div>
          <Button variant="outline" onClick={clearSelection} className="flex items-center gap-2">
            <RotateCcw className="w-4 h-4" />
            초기화
          </Button>
        </header>

        <main className="grid grid-cols-1 md:grid-cols-12 gap-6 h-[calc(100vh-140px)]">
          {/* Left Column - Lecture Selection & Action */}
          <div className="md:col-span-4 flex flex-col gap-4 h-full overflow-hidden">
            <div className="bg-white p-4 rounded-xl shadow-sm border overflow-hidden flex-1 flex flex-col">
              <LectureList />
            </div>
            <div className="shrink-0 bg-white rounded-xl shadow-sm border">
              <OptimizationPanel />
            </div>
          </div>

          {/* Right Column - Timetable */}
          <div className="md:col-span-8 h-full overflow-hidden flex flex-col bg-white rounded-xl shadow-sm border p-4 relative">
            <div className="flex justify-between items-center mb-4 shrink-0">
              <h2 className="text-xl font-bold">Timetable</h2>
              <div className="text-sm">
                {optimizedSchedule ? (
                  <span className="text-primary font-semibold flex items-center">
                    Quantum Optimized Schedule
                  </span>
                ) : (
                  <span className="text-muted-foreground">Manual Selection Draft</span>
                )}
              </div>
            </div>
            <div className="flex-1 min-h-0">
              <TimetableView schedule={optimizedSchedule || selectedLectures} />
            </div>

            <div className="shrink-0 mt-4">
              <OptimizationDetails />
            </div>
          </div>
        </main>

        {hasOptimizationRuns && (
          <div className="mt-8">
            <TimetableCardsRow />
          </div>
        )}

      </div>
    </div>
  );
}
