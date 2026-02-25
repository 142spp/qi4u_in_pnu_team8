"use client";

import { useLectureStore } from "@/store/useLectureStore";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ChevronDown, ChevronUp, Settings2 } from "lucide-react";

const FASTAPI_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function OptimizationPanel() {
    const { selectedIds, targetCredits, setOptimizedSchedule, setTargetCredits } = useLectureStore();
    const [taskId, setTaskId] = useState<string | null>(null);
    const [showSettings, setShowSettings] = useState(false);

    // Form inputs state
    const [config, setConfig] = useState({
        max_candidates: 300,
        total_reads: 100,
        batch_size: 100,
        w_hard_overlap: 10000.0,
        w_target_credit: 10.0,
        w_mandatory: -10000.0,
        w_first_class: 50.0,
        w_lunch_overlap: 30.0,
        r_free_day: 100.0,
        p_free_day_break: 500.0,
        w_contiguous_reward: -20.0,
        w_tension_base: 5.0
    });

    const handleConfigChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setConfig(prev => ({
            ...prev,
            [name]: parseFloat(value) || 0
        }));
    };

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
            setOptimizedSchedule(taskStatus.result.schedule, taskStatus.result);
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
                ...config
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

    const renderInput = (label: string, name: keyof typeof config, step = "1") => (
        <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase font-bold text-muted-foreground">{label}</label>
            <input
                type="number"
                name={name}
                value={config[name]}
                onChange={handleConfigChange}
                step={step}
                className="w-full border rounded px-2 py-1 text-sm bg-gray-50 focus:bg-white transition-colors"
                disabled={taskStatus?.status === "PROCESSING" || taskStatus?.status === "PENDING"}
            />
        </div>
    );

    return (
        <div className="flex flex-col p-4 w-full h-full">
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-lg">Quantum Parameters</h3>
                <button
                    onClick={() => setShowSettings(!showSettings)}
                    className="flex items-center gap-1 text-xs font-semibold text-primary/70 hover:text-primary transition-colors bg-primary/10 px-2 py-1 rounded"
                >
                    <Settings2 className="w-3 h-3" />
                    Tweak Parameters {showSettings ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
            </div>

            {/* Always visible basic controls */}
            <div className="mb-4">
                <div className="flex flex-col gap-1">
                    <label className="text-xs font-bold text-muted-foreground">Target Credits</label>
                    <input
                        type="number"
                        value={targetCredits}
                        onChange={(e) => setTargetCredits(parseFloat(e.target.value) || 0)}
                        className="w-full border rounded px-3 py-2 text-sm focus:outline-primary transition-all font-semibold"
                        disabled={taskStatus?.status === "PROCESSING" || taskStatus?.status === "PENDING"}
                    />
                </div>
            </div>

            {/* Collapsible advanced settings area */}
            <div className={`transition-all duration-300 overflow-hidden flex-1 flex flex-col ${showSettings ? 'opacity-100 max-h-[800px] mb-4' : 'opacity-0 max-h-0'}`}>
                <div className="overflow-y-auto pr-2 flex-1 pb-2 scrollbar-thin space-y-4">
                    <div className="p-3 bg-muted/50 rounded border space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-primary border-b pb-1">Compute Limits</h4>
                        <div className="grid grid-cols-2 gap-3">
                            {renderInput("Candidates List Size", "max_candidates", "10")}
                            {renderInput("Total Reads", "total_reads", "50")}
                            {renderInput("Batch Size", "batch_size", "50")}
                        </div>
                    </div>

                    <div className="p-3 bg-muted/50 rounded border space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-orange-500 border-b pb-1">Penalty Weights (+)</h4>
                        <div className="grid grid-cols-2 gap-3">
                            {renderInput("Hard Overlap Eval", "w_hard_overlap", "1000")}
                            {renderInput("Credits Variance", "w_target_credit", "1")}
                            {renderInput("1st Period Cost", "w_first_class", "5")}
                            {renderInput("Lunch Overlap", "w_lunch_overlap", "5")}
                            {renderInput("Free Day Break", "p_free_day_break", "10")}
                            {renderInput("Tension Base Eq.", "w_tension_base", "1")}
                        </div>
                    </div>

                    <div className="p-3 bg-muted/50 rounded border space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-green-600 border-b pb-1">Reward Weights (-)</h4>
                        <div className="grid grid-cols-2 gap-3">
                            {renderInput("Mandatory Reward", "w_mandatory", "1000")}
                            {renderInput("Free Day Reward", "r_free_day", "10")}
                            {renderInput("Contiguous Class", "w_contiguous_reward", "1")}
                        </div>
                    </div>
                </div>
            </div>

            {/* Actions panel locked to bottom */}
            <div className="space-y-4 shrink-0 mt-auto pt-2 border-t">
                <Button
                    className="w-full h-12 text-md font-semibold bg-primary hover:opacity-90 transition-all text-primary-foreground shadow-lg"
                    onClick={handleOptimize}
                    disabled={selectedIds.length === 0 || taskStatus?.status === "PROCESSING" || taskStatus?.status === "PENDING"}
                >
                    {taskStatus?.status === "PROCESSING" ? "Optimizing..." : "Run Quantum Optimization"}
                </Button>

                {taskId && taskStatus && (
                    <div className="space-y-2 p-3 bg-gray-50 rounded-lg border">
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">Status: {taskStatus.status}</span>
                            <span className="text-xs text-muted-foreground">ID: {taskId.substring(0, 8)}</span>
                        </div>
                        <Progress value={getProgress(taskStatus.status)} className="h-2" />
                        {taskStatus.summary && (
                            <p className="text-[10px] text-muted-foreground italic truncate">
                                {taskStatus.summary}
                            </p>
                        )}
                    </div>
                )}

                {taskStatus?.status === "FAILURE" && (
                    <div className="p-3 bg-destructive/10 text-destructive rounded-lg border border-destructive/20 mt-2 text-sm">
                        <p className="font-bold">Optimization Failed</p>
                        <p className="text-xs mt-1 truncate">{taskStatus.error}</p>
                    </div>
                )}
            </div>

        </div>
    );
}
