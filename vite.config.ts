import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit(),
		VitePWA({
			registerType: 'autoUpdate',
			manifest: {
				name: 'Station One',
				short_name: 'Station One',
				description: 'Seu centro de atenção pessoal',
				theme_color: '#000000',
				background_color: '#000000',
				display: 'standalone',
				start_url: '/',
				icons: [
					{ src: '/icons/96.png', sizes: '96x96', type: 'image/png' },
					{ src: '/icons/128.png', sizes: '128x128', type: 'image/png' }
				]
			}
		})
	]
});
