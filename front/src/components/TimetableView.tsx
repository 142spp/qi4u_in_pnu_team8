"use client";

import { useLectureStore, Lecture } from "@/store/useLectureStore";
import { parseTimeRoom } from "@/lib/timeParser";
import React, { useMemo } from "react";
import { X } from "lucide-react";

interface TimetableViewProps {
    schedule: Lecture[];
    readonly?: boolean;
}

const DAYS = ["월", "화", "수", "목", "금"];
const START_HOUR = 8;
const END_HOUR = 20;
const HOUR_HEIGHT = 60; // pixels per hour
const TOTAL_HOURS = END_HOUR - START_HOUR;

// Colors for different categories sequentially assigned
const getBgColor = (index: number) => {
    const colors = [
        "bg-primary/20 border-primary/40 text-primary-foreground",
        "bg-blue-500/20 border-blue-500/40 text-blue-900",
        "bg-green-500/20 border-green-500/40 text-green-900",
        "bg-orange-500/20 border-orange-500/40 text-orange-900",
        "bg-purple-500/20 border-purple-500/40 text-purple-900",
        "bg-pink-500/20 border-pink-500/40 text-pink-900",
        "bg-teal-500/20 border-teal-500/40 text-teal-900",
        "bg-yellow-500/20 border-yellow-500/40 text-yellow-900",
        "bg-indigo-500/20 border-indigo-500/40 text-indigo-900",
        "bg-rose-500/20 border-rose-500/40 text-rose-900",
        "bg-cyan-500/20 border-cyan-500/40 text-cyan-900",
        "bg-emerald-500/20 border-emerald-500/40 text-emerald-900",
    ];
    return colors[index % colors.length];
};

export default function TimetableView({ schedule, readonly = false }: TimetableViewProps) {
    const { toggleSelection } = useLectureStore();
    // Parse all lectures into renderable blocks
    const renderedBlocks = useMemo(() => {
        const blocks: any[] = [];
        schedule.forEach((lec, index) => {
            const timeBlocks = parseTimeRoom(lec.time_room);
            timeBlocks.forEach((tb, tbIndex) => {
                // If it starts before 9, clamp it.
                if (tb.startMinutes < START_HOUR * 60) return;

                const startOffsetHours = (tb.startMinutes - START_HOUR * 60) / 60;
                const durationHours = (tb.endMinutes - tb.startMinutes) / 60;

                blocks.push({
                    id: `${lec.id}-${tb.dayIndex}-${tbIndex}`,
                    lecture: lec,
                    lectureIndex: index,
                    dayIndex: tb.dayIndex,
                    top: startOffsetHours * HOUR_HEIGHT,
                    height: durationHours * HOUR_HEIGHT,
                });
            });
        });
        return blocks;
    }, [schedule]);

    return (
        <div className="w-full h-full flex flex-col bg-white border rounded-xl overflow-hidden shadow-sm">
            <div className="flex bg-muted text-muted-foreground border-b select-none">
                <div className="w-16 shrink-0 border-r" /> {/* Time column header header */}
                {DAYS.map((day) => (
                    <div key={day} className="flex-1 text-center py-2 text-sm font-semibold border-r last:border-r-0">
                        {day}
                    </div>
                ))}
            </div>

            <div className="flex-1 overflow-y-auto min-h-0 bg-white">
                <div className="flex w-full mt-4 mb-8 relative" style={{ height: TOTAL_HOURS * HOUR_HEIGHT }}>
                    {/* Time labels axis */}
                    <div className="w-16 shrink-0 border-r flex flex-col relative">
                        {Array.from({ length: TOTAL_HOURS + 1 }).map((_, i) => (
                            <div key={i} className="text-xs text-muted-foreground text-right pr-2 absolute w-full" style={{ top: i * HOUR_HEIGHT - 8 }}>
                                {START_HOUR + i}:00
                            </div>
                        ))}
                    </div>

                    {/* Grid Container */}
                    <div className="flex-1 relative">
                        {/* Horizontal Grid lines */}
                        {Array.from({ length: TOTAL_HOURS + 1 }).map((_, i) => (
                            <div key={i} className="absolute w-full border-t border-gray-100" style={{ top: i * HOUR_HEIGHT }} />
                        ))}

                        {/* Vertical Column dividers */}
                        {DAYS.map((_, i) => (
                            <div key={i} className="absolute h-full border-r border-gray-100" style={{ left: `${(100 / 5) * i}%`, width: `${100 / 5}%` }} />
                        ))}

                        {/* Lecture Blocks */}
                        {renderedBlocks.map((block) => (
                            <div
                                key={block.id}
                                className={`absolute left-0 right-0 mx-1 p-1.5 rounded text-xs border overflow-hidden leading-tight group ${getBgColor(block.lectureIndex)}`}
                                style={{
                                    top: block.top,
                                    height: block.height - 2,
                                    left: `calc(${(100 / 5) * block.dayIndex}% + 0.25rem)`,
                                    width: `calc(${100 / 5}% - 0.5rem)`,
                                    zIndex: 10
                                }}
                                title={`${block.lecture.name} (${block.lecture.credit}학점)\n${block.lecture.professor}\n${block.lecture.time_room}`}
                            >
                                {!readonly && (
                                    <button
                                        onClick={(e: React.MouseEvent) => {
                                            e.stopPropagation();
                                            toggleSelection(block.lecture.id);
                                        }}
                                        className="absolute top-1 right-1 p-0.5 rounded-full bg-black/10 hover:bg-black/20 text-black/60 hover:text-black opacity-0 group-hover:opacity-100 transition-opacity"
                                        title="강의 제외"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                )}
                                <div className={`font-bold truncate ${!readonly ? 'pr-4' : ''}`}>{block.lecture.name} <span className="font-normal text-[10px]">({block.lecture.credit}학점)</span></div>
                                <div className="text-[10px] truncate opacity-80">{block.lecture.professor}</div>
                                <div className="text-[10px] truncate opacity-60">
                                    {Math.floor(block.top / HOUR_HEIGHT) + START_HOUR}:{Math.floor((block.top % HOUR_HEIGHT) / HOUR_HEIGHT * 60).toString().padStart(2, '0')} -
                                    {Math.floor((block.top + block.height) / HOUR_HEIGHT) + START_HOUR}:{Math.floor(((block.top + block.height) % HOUR_HEIGHT) / HOUR_HEIGHT * 60).toString().padStart(2, '0')}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
