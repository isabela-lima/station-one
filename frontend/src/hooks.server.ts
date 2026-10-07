import type { Handle } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

// O navegador só conhece um endereço (o do Tailscale, ou localhost em dev).
// Tudo em /api/* é repassado para o FastAPI, que escuta só em 127.0.0.1.
const API_INTERNAL_URL = env.API_INTERNAL_URL ?? 'http://127.0.0.1:8000';

// Cabeçalhos "hop-by-hop" não podem ser repassados entre conexões
const HOP_BY_HOP = new Set([
	'connection',
	'keep-alive',
	'transfer-encoding',
	'upgrade',
	'proxy-authenticate',
	'proxy-authorization',
	'te',
	'trailer',
	'host',
	'content-length'
]);

function forwardHeaders(source: Headers, skip: Set<string> = HOP_BY_HOP): Headers {
	const out = new Headers();
	source.forEach((value, key) => {
		if (!skip.has(key.toLowerCase())) out.set(key, value);
	});
	return out;
}

// O fetch do Node já descompacta a resposta: repassar content-encoding faria o
// navegador tentar descompactar de novo
const RESPONSE_SKIP = new Set([...HOP_BY_HOP, 'content-encoding']);

export const handle: Handle = async ({ event, resolve }) => {
	const { pathname, search } = event.url;
	if (pathname !== '/api' && !pathname.startsWith('/api/')) return resolve(event);

	const target = `${API_INTERNAL_URL}${pathname.slice('/api'.length) || '/'}${search}`;
	const method = event.request.method;
	const hasBody = method !== 'GET' && method !== 'HEAD';

	try {
		const upstream = await fetch(target, {
			method,
			headers: forwardHeaders(event.request.headers),
			body: hasBody ? event.request.body : undefined,
			// Necessário para repassar o corpo como stream
			// @ts-expect-error — `duplex` ainda não está nos tipos do RequestInit
			duplex: hasBody ? 'half' : undefined,
			redirect: 'manual'
		});
		// O corpo segue como stream (respostas longas, e streaming do assistente no futuro)
		return new Response(upstream.body, {
			status: upstream.status,
			statusText: upstream.statusText,
			headers: forwardHeaders(upstream.headers, RESPONSE_SKIP)
		});
	} catch {
		return new Response(JSON.stringify({ detail: 'API indisponível' }), {
			status: 502,
			headers: { 'content-type': 'application/json' }
		});
	}
};
