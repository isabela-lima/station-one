// Roda com `pnpm test` (node --test, sem dependências). Fixa "hoje" para ser determinístico;
// o CI roda em UTC e localmente em America/Sao_Paulo — os dois têm que passar.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
	addDaysISO,
	compareByUrgency,
	daysBetween,
	dueInfo,
	nextWeekdayISO,
	parseISODate,
	toISODate
} from './dates.ts';

const today = '2026-10-07'; // quarta-feira

test('ida e volta de data não escorrega de dia', () => {
	assert.equal(toISODate(parseISODate('2026-10-10')), '2026-10-10');
});

test('soma de dias atravessa mês e fevereiro', () => {
	assert.equal(addDaysISO('2026-10-31', 1), '2026-11-01');
	assert.equal(addDaysISO('2026-02-28', 1), '2026-03-01');
	assert.equal(daysBetween(today, '2026-10-06'), -1);
});

test('próximo dia da semana; o próprio dia vira a semana seguinte', () => {
	assert.equal(nextWeekdayISO(5, today), '2026-10-09');
	assert.equal(nextWeekdayISO(3, today), '2026-10-14');
});

test('rótulo e tom do prazo', () => {
	assert.deepEqual(dueInfo('2026-10-06', today), { label: 'ontem', tone: 'overdue' });
	assert.equal(dueInfo('2026-10-01', today).tone, 'overdue');
	assert.deepEqual(dueInfo(today, today), { label: 'hoje', tone: 'today' });
	assert.deepEqual(dueInfo('2026-10-08', today), { label: 'amanhã', tone: 'soon' });
	assert.equal(dueInfo('2026-10-09', today).label, 'sex');
	assert.equal(dueInfo('2026-10-20', today).tone, 'later');
});

test('urgência: atrasadas, por data, foco, sem prazo', () => {
	const order = [
		{ id: 'sem', due_date: null, priority: false },
		{ id: 'foco', due_date: null, priority: true },
		{ id: 'dia10', due_date: '2026-10-10', priority: false },
		{ id: 'atrasada', due_date: '2026-10-01', priority: false }
	]
		.sort(compareByUrgency)
		.map((t) => t.id);
	assert.deepEqual(order, ['atrasada', 'dia10', 'foco', 'sem']);
});
