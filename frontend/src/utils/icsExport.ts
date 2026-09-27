import { createEvent, type DateArray } from 'ics';
import type { MeetingDetail } from '../types';

export function generateIcsFile(meeting: MeetingDetail, summaryText?: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const startDate = new Date(meeting.started_at);
    const startArray: DateArray = [
      startDate.getUTCFullYear(),
      startDate.getUTCMonth() + 1,
      startDate.getUTCDate(),
      startDate.getUTCHours(),
      startDate.getUTCMinutes(),
    ];

    const durationMinutes = Math.max(1, Math.floor((meeting.duration_seconds || 1800) / 60));
    const hours = Math.floor(durationMinutes / 60);
    const minutes = durationMinutes % 60;

    let description = `SonoScribe Session: ${meeting.title}\nDuration: ${durationMinutes} minutes\n`;
    if (summaryText) {
      description += `\n--- Executive Summary ---\n${summaryText}\n`;
    }
    if (meeting.segments && meeting.segments.length > 0) {
      description += `\n--- Transcript Snippet ---\n`;
      description += meeting.segments.slice(0, 10).map((s) => s.text).join('\n');
    }

    createEvent(
      {
        title: meeting.title,
        description: description,
        start: startArray,
        duration: { hours, minutes },
        location: 'SonoScribe Audio Session',
        status: 'CONFIRMED',
        categories: ['Meeting', 'SonoScribe'],
      },
      (error, value) => {
        if (error || !value) {
          reject(error || new Error('Failed to create ICS event'));
        } else {
          resolve(value);
        }
      }
    );
  });
}
