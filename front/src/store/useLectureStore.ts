import { create } from 'zustand';
import { parseTimetableString, checkOverlap } from '@/utils/timeUtils';

export interface Lecture {
    id: string;
    number: string;
    class_num: string;
    name: string;
    credit: number;
    time_room: string;
    professor: string;
    category: string;
}

interface LectureState {
    lectures: Lecture[];
    selectedIds: string[];
    optimizedSchedule: Lecture[] | null;
    optimizationResult: any | null; // Stores energy, breakdown, etc.
    targetCredits: number;
    setLectures: (lectures: Lecture[]) => void;
    toggleSelection: (id: string) => void;
    clearSelection: () => void;
    setOptimizedSchedule: (schedule: Lecture[] | null, result?: any) => void;
    setTargetCredits: (credits: number) => void;
}

export const useLectureStore = create<LectureState>((set) => ({
    lectures: [],
    selectedIds: [],
    optimizedSchedule: null,
    optimizationResult: null,
    targetCredits: 18, // default target
    setLectures: (lectures) => set({ lectures }),
    toggleSelection: (id) => set((state) => {
        // clear optimized schedule when user modifies selection
        if (state.selectedIds.includes(id)) {
            return { selectedIds: state.selectedIds.filter(v => v !== id), optimizedSchedule: null, optimizationResult: null };
        } else {
            // Overlap Validation Check
            const newLecture = state.lectures.find(l => l.id === id);
            if (newLecture) {
                const newIntervals = parseTimetableString(newLecture.time_room);

                // Check against all currently selected lectures
                for (const existingId of state.selectedIds) {
                    const existingLec = state.lectures.find(l => l.id === existingId);
                    if (existingLec) {
                        const existingIntervals = parseTimetableString(existingLec.time_room);
                        if (checkOverlap(newIntervals, existingIntervals)) {
                            alert(`선택하신 강의 [${newLecture.name}]는 기존 선택된 강의 [${existingLec.name}]와(과) 시간이 겹칩니다! 선택할 수 없습니다.`);
                            return state; // Cancel selection modification
                        }
                    }
                }
            }
            return { selectedIds: [...state.selectedIds, id], optimizedSchedule: null, optimizationResult: null };
        }
    }),
    clearSelection: () => set({ selectedIds: [], optimizedSchedule: null, optimizationResult: null }),
    setOptimizedSchedule: (schedule, result = null) => set((state: LectureState) => ({
        optimizedSchedule: schedule,
        optimizationResult: result,
        selectedIds: schedule ? schedule.map((l: Lecture) => l.id) : state.selectedIds
    })),
    setTargetCredits: (credits) => set({ targetCredits: credits })
}));
