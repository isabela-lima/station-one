<script lang="ts">
  import { onMount } from "svelte";

  import "./app.css";

  let currentDate = "";
  let currentTime = "";

  function updateDateTime() {
    const now = new Date();

    currentDate = now.toLocaleDateString("pt-BR", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });

    currentTime = now.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  onMount(() => {
    updateDateTime();
    const timer = setInterval(updateDateTime, 1000);

    return () => clearInterval(timer);
  });
</script>

<div
  class="h-screen bg-slate-900 text-slate-100 grid grid-cols-[1fr_350px] font-sans"
>
  <div class="flex flex-col">
    <header class="p-8">
      <div class="text-right">
        <div class="text-7xl font-bold">{currentTime}</div>
        <div class="text-xl text-slate-400">{currentDate}</div>
      </div>
    </header>

    <main class="flex-grow p-8 overflow-y-auto"></main>
  </div>

  <aside class="bg-slate-800 p-8 border-l border-slate-700 overflow-y-auto">
    <h2 class="text-2xl font-bold mb-6">Adicionar Item</h2>
    <form>
      <div></div>
    </form>
  </aside>
</div>

<style>
  :global(body) {
    font-family: "Inter", sans-serif;
  }
</style>
