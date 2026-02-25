import { create } from 'zustand';

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
    targetCredits: number;
    setLectures: (lectures: Lecture[]) => void;
    toggleSelection: (id: string) => void;
    clearSelection: () => void;
    setOptimizedSchedule: (schedule: Lecture[] | null) => void;
    setTargetCredits: (credits: number) => void;
}

export const useLectureStore = create<LectureState>((set) => ({
    lectures: [],
    selectedIds: [],
    optimizedSchedule: null,
    targetCredits: 18, // default target
    setLectures: (lectures) => set({ lectures }),
    toggleSelection: (id) => set((state) => {
        // clear optimized schedule when user modifies selection
        if (state.selectedIds.includes(id)) {
            return { selectedIds: state.selectedIds.filter(v => v !== id), optimizedSchedule: null };
        } else {
            return { selectedIds: [...state.selectedIds, id], optimizedSchedule: null };
        }
    }),
    clearSelection: () => set({ selectedIds: [], optimizedSchedule: null }),
    setOptimizedSchedule: (schedule) => set({ optimizedSchedule: schedule }),
    setTargetCredits: (credits) => set({ targetCredits: credits })
}));
