export interface ParsedTimeBlock {
    dayIndex: number; // 0=Mon, 4=Fri
    startMinutes: number; // minutes from 00:00
    endMinutes: number;
}

const DAYS = ["월", "화", "수", "목", "금"];

export function parseTimeRoom(timeStr: string): ParsedTimeBlock[] {
    const blocks: ParsedTimeBlock[] = [];
    if (!timeStr) return blocks;

    // e.g "금 09:00(50)(외부)..., 토 14:00-17:00..."
    const segments = timeStr.split(",");
    for (const segment of segments) {
        const seg = segment.trim();

        // Find day
        let dayIndex = -1;
        for (let i = 0; i < DAYS.length; i++) {
            if (seg.startsWith(DAYS[i])) {
                dayIndex = i;
                break;
            }
        }

        // Only process Mon-Fri
        if (dayIndex === -1) continue;

        // MATCH: HH:MM-HH:MM or HH:MM(duration)
        const regex = /(\d{2}):(\d{2})(?:-(\d{2}):(\d{2})|\((\d+)\))/;
        const match = seg.match(regex);

        if (match) {
            const startH = parseInt(match[1]);
            const startM = parseInt(match[2]);
            const startMinutes = startH * 60 + startM;

            let endMinutes = 0;
            if (match[3] && match[4]) {
                // HH:MM-HH:MM format
                const endH = parseInt(match[3]);
                const endM = parseInt(match[4]);
                endMinutes = endH * 60 + endM;
            } else if (match[5]) {
                // HH:MM(duration) format
                const duration = parseInt(match[5]);
                endMinutes = startMinutes + duration;
            }

            blocks.push({ dayIndex, startMinutes, endMinutes });
        }
    }

    return blocks;
}
