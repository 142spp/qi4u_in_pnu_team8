"use client";

import { Lecture } from "@/store/useLectureStore";
import { parseTimeRoom } from "@/lib/timeParser";
import { useMemo } from "react";

interface MiniTimetableProps {
    schedule: Lecture[];
}

const START_HOUR = 8;
const END_HOUR = 20;
const TOTAL_HOURS = END_HOUR - START_HOUR;

const getBgColor = (index: number) => {
    const colors = [
        "bg-primary/40",
        "bg-blue-500/40",
        "bg-green-500/40",
        "bg-orange-500/40",
        "bg-purple-500/40",
        "bg-pink-500/40",
        "bg-teal-500/40",
        "bg-yellow-500/40",
        "bg-indigo-500/40",
        "bg-rose-500/40",
        "bg-cyan-500/40",
        "bg-emerald-500/40",
    ];
    return colors[index % colors.length];
};

export default function MiniTimetable({ schedule }: MiniTimetableProps) {
    const renderedBlocks = useMemo(() => {
        const blocks: any[] = [];
        schedule.forEach((lec, index) => {
            const timeBlocks = parseTimeRoom(lec.time_room);
            timeBlocks.forEach((tb, tbIndex) => {
                if (tb.startMinutes < START_HOUR * 60) return;

                const startOffsetHours = (tb.startMinutes - START_HOUR * 60) / 60;
                const durationHours = (tb.endMinutes - tb.startMinutes) / 60;

                blocks.push({
                    id: `${lec.id}-${tb.dayIndex}-${tbIndex}`,
                    lectureIndex: index,
                    dayIndex: tb.dayIndex,
                    topPercent: (startOffsetHours / TOTAL_HOURS) * 100,
                    heightPercent: (durationHours / TOTAL_HOURS) * 100,
                });
            });
        });
        return blocks;
    }, [schedule]);

    return (
        <div className="w-full aspect-[4/5] bg-gray-50 border rounded-md relative overflow-hidden">
            {/* Vertical grid lines */}
            <div className="absolute inset-0 flex border-t">
                {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex-1 border-r border-gray-200 last:border-r-0 h-full" />
                ))}
            </div>

            {/* Horizontal grid lines */}
            <div className="absolute inset-0 flex flex-col pointer-events-none">
                {Array.from({ length: TOTAL_HOURS }).map((_, i) => (
                    <div key={i} className="flex-1 border-b border-gray-100 last:border-b-0 w-full" />
                ))}
            </div>

            {/* Blocks */}
            {renderedBlocks.map((block) => (
                <div
                    key={block.id}
                    className={`absolute rounded-xs mx-px ${getBgColor(block.lectureIndex)}`}
                    style={{
                        top: `${block.topPercent}%`,
                        height: `${block.heightPercent}%`,
                        left: `${(100 / 5) * block.dayIndex}%`,
                        width: `calc(${100 / 5}% - 2px)`,
                    }}
                />
            ))}
        </div>
    );
}
