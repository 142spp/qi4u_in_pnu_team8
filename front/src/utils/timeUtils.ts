export interface TimeInterval {
    day: string;
    start: number; // minutes from midnight
    end: number;   // minutes from midnight
}

/**
 * Parses time strings from the backend format into structured intervals.
 * E.g. "화 16:30(75)", "수 13:30-16:30"
 */
export function parseTimetableString(schedStr: string | null | undefined): TimeInterval[] {
    if (!schedStr) return [];

    const intervals: TimeInterval[] = [];

    // 1. format: 화 16:30(75) 507-102
    const pattern1 = /([월화수목금토일])\s*(\d{2}):(\d{2})\((\d+)\)/g;
    let match1;
    while ((match1 = pattern1.exec(schedStr)) !== null) {
        const day = match1[1];
        const startMin = parseInt(match1[2], 10) * 60 + parseInt(match1[3], 10);
        const duration = parseInt(match1[4], 10);
        intervals.push({ day, start: startMin, end: startMin + duration });
    }

    // 2. format: 수 13:30-16:30 밀양M03-3350
    const pattern2 = /([월화수목금토일])\s*(\d{2}):(\d{2})-(\d{2}):(\d{2})/g;
    let match2;
    while ((match2 = pattern2.exec(schedStr)) !== null) {
        const day = match2[1];
        const startMin = parseInt(match2[2], 10) * 60 + parseInt(match2[3], 10);
        const endMin = parseInt(match2[4], 10) * 60 + parseInt(match2[5], 10);
        intervals.push({ day, start: startMin, end: endMin });
    }

    return intervals;
}

/**
 * Checks if two intervals overlap
 */
export function checkOverlap(list1: TimeInterval[], list2: TimeInterval[]): boolean {
    for (const time1 of list1) {
        for (const time2 of list2) {
            if (time1.day === time2.day) {
                const maxStart = Math.max(time1.start, time2.start);
                const minEnd = Math.min(time1.end, time2.end);
                if (maxStart < minEnd) {
                    return true;
                }
            }
        }
    }
    return false;
}
