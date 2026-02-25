"use client";

import { useLectureStore } from "@/store/useLectureStore";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useEffect, useState } from "react";
import { toast } from "sonner";

const FASTAPI_URL = "http://localhost:8000/api";

export default function OptimizationPanel() {
    const { selectedIds, targetCredits, setOptimizedSchedule } = useLectureStore();
    const [taskId, setTaskId] = useState<string | null>(null);

    const totalCredits = 0; // Optimization panel doesn't strictly need this now, or compute from selectedIds length

    // Status Polling Query
    const { data: taskStatus, refetch } = useQuery({
        queryKey: ['optimize-task', taskId],
        queryFn: async () => {
            const res = await axios.get(`${FASTAPI_URL}/optimize/${taskId}`);
            return res.data;
        },
        enabled: !!taskId,
        refetchInterval: (query) => {
            const status = query.state?.data?.status;
            if (status === 'SUCCESS' || status === 'FAILURE') return false;
            return 1000; // Poll every 1s
        }
    });

    useEffect(() => {
        if (taskStatus?.status === 'SUCCESS' && taskStatus.result?.schedule) {
            setOptimizedSchedule(taskStatus.result.schedule);
            toast.success(`Optimization Completed! Energy: ${taskStatus.result.energy}`);
        }
    }, [taskStatus, setOptimizedSchedule]);

    const handleOptimize = async () => {
        if (selectedIds.length === 0) {
            toast.error("Please select at least one lecture.");
            return;
        }

        try {
            const res = await axios.post(`${FASTAPI_URL}/optimize`, {
                selected_lecture_ids: selectedIds,
                target_credits: targetCredits,
            });
            setTaskId(res.data.task_id);
            toast.success("Optimization task started!");
            refetch();
        } catch (err) {
            toast.error("Failed to start optimization");
        }
    };

    const getProgress = (status?: string) => {
        if (status === "PENDING") return 30;
        if (status === "PROCESSING") return 70;
        if (status === "SUCCESS") return 100;
        return 0;
    };

    return (
        <div className="flex flex-col p-4 w-full">

            {/* Actions panel */}
            <div className="space-y-4 shrink-0">
                <Button
                    className="w-full h-12 text-md font-semibold bg-primary hover:opacity-90 transition-all text-primary-foreground shadow-lg"
                    onClick={handleOptimize}
                    disabled={selectedIds.length === 0 || taskStatus?.status === "PROCESSING" || taskStatus?.status === "PENDING"}
                >
                    {taskStatus?.status === "PROCESSING" ? "Optimizing..." : "Run Quantum Optimization"}
                </Button>

                {taskId && taskStatus && (
                    <div className="space-y-2 p-3 bg-gray-50 rounded-lg border mt-2">
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">Status: {taskStatus.status}</span>
                            <span className="text-xs text-muted-foreground">ID: {taskId.substring(0, 8)}</span>
                        </div>
                        <Progress value={getProgress(taskStatus.status)} className="h-2" />
                    </div>
                )}
            </div>

            {taskStatus?.status === "FAILURE" && (
                <div className="p-3 bg-destructive/10 text-destructive rounded-lg border border-destructive/20 mt-4">
                    <p className="font-bold text-sm">Optimization Failed</p>
                    <p className="text-xs mt-1">{taskStatus.error}</p>
                </div>
            )}
        </div>
    );
}
