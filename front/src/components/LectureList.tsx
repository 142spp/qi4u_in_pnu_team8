"use client";

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useLectureStore, Lecture } from '@/store/useLectureStore';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Search } from 'lucide-react';
import React, { useEffect, useState, useMemo } from 'react';

const FASTAPI_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function LectureList() {
    const { lectures, setLectures, selectedIds, toggleSelection, targetCredits, setTargetCredits } = useLectureStore();
    const [searchTerm, setSearchTerm] = useState('');
    const [debouncedTerm, setDebouncedTerm] = useState('');

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedTerm(searchTerm);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchTerm]);

    const { data, isLoading, error } = useQuery({
        queryKey: ['lectures'],
        queryFn: async () => {
            const res = await axios.get(`${FASTAPI_URL}/lectures`);
            return res.data.lectures as Lecture[];
        }
    });

    useEffect(() => {
        if (data) {
            setLectures(data);
        }
    }, [data, setLectures]);

    const filteredLectures = useMemo(() => {
        if (!debouncedTerm) return lectures.slice(0, 100); // Only render top 100 initially to prevent DOM lag

        const term = debouncedTerm.toLowerCase();
        const filtered = lectures.filter(l =>
            l.name.toLowerCase().includes(term) ||
            l.number.toLowerCase().includes(term)
        );

        return filtered.slice(0, 100); // Limit to 100 results
    }, [lectures, debouncedTerm]);

    if (isLoading) return (
        <div className="space-y-4 p-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
        </div>
    );

    if (error) return <div className="p-4 text-destructive">Failed to load lectures. Is the backend running?</div>;

    return (
        <div className="flex flex-col h-full space-y-4">
            <div className="flex items-center gap-2">
                <div className="flex-1 flex items-center space-x-2 border rounded-md px-3 py-2 bg-white">
                    <Search className="w-5 h-5 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Search by class name or code..."
                        value={searchTerm}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                        className="flex-1 outline-none bg-transparent text-sm text-foreground"
                    />
                </div>
            </div>
            <ScrollArea className="flex-1 border-t overflow-y-auto min-h-0">
                <div className="flex flex-col divide-y divide-gray-100">
                    {filteredLectures.map((lec) => (
                        <div key={lec.id} className="flex items-start space-x-3 p-4 hover:bg-gray-50 transition-colors">
                            <Checkbox
                                id={lec.id}
                                checked={selectedIds.includes(lec.id)}
                                onCheckedChange={() => toggleSelection(lec.id)}
                            />
                            <div className="flex flex-col flex-1">
                                <label htmlFor={lec.id} className="text-sm font-medium leading-none cursor-pointer">
                                    {lec.name} <span className="text-muted-foreground">({lec.number}-{lec.class_num})</span>
                                </label>
                                <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                                    <Badge variant="outline" className="text-muted-foreground bg-muted border-muted">{lec.category}</Badge>
                                    <span className="flex items-center text-nowrap">{lec.credit} Credits</span>
                                    <span className="flex items-center text-nowrap">{lec.professor}</span>
                                    <span className="flex items-center text-nowrap font-medium text-foreground">{lec.time_room}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
}
