<script lang="ts">
  import { itemsStorage } from "@/lib/storage";
  import { onMount } from "svelte";
  import "./app.css";
  import ItemCard from "./ItemCard.svelte";
  import type { Item } from "./types";

  // --- Estado da Aplicação ---
  let items: Item[] = [];
  let currentDate = "";
  let currentTime = "";

  // --- Estado do Formulário ---
  let selectedType: Item["type"] = "note";
  let content = "";

  // --- Funções ---
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

  async function handleSubmit() {
    if (!content.trim()) return;

    const newItem: Item = {
      id: Date.now(),
      type: selectedType,
      content: content.trim(),
      completed: selectedType === "task" ? false : undefined,
    };

    items = [...items, newItem];
    await itemsStorage.setValue(items);
    content = "";
  }

  async function handleToggleTask(event: CustomEvent<{ id: number }>) {
    const { id } = event.detail;
    items = items.map((item) =>
      item.id === id ? { ...item, completed: !item.completed } : item
    );
    await itemsStorage.setValue(items);
  }

  // --- Ciclo de Vida ---
  onMount(() => {
    (async () => {
      items = await itemsStorage.getValue();
    })();

    updateDateTime();
    const timer = setInterval(updateDateTime, 1000);

    return () => clearInterval(timer);
  });
</script>

<div class="h-screen grid grid-cols-[1fr_350px] font-sans">
  <div class="flex flex-col">
    <header class="p-8">
      <div class="text-right">
        <div class="text-7xl font-bold">{currentTime}</div>
        <div class="text-xl text-slate-400">{currentDate}</div>
      </div>
    </header>

    <main class="flex-grow p-8 overflow-y-auto space-y-4">
      <!-- 3. O loop agora é muito mais limpo! -->
      {#each items as item (item.id)}
        <ItemCard {item} on:toggle={handleToggleTask} />
      {/each}
    </main>
  </div>

  <aside class="p-8 overflow-y-auto flex w-full">
    <div class="divider divider-horizontal"></div>
    <div>
      <h2 class="text-2xl font-bold mb-6">Adicionar Item</h2>
      <form class="space-y-4" on:submit|preventDefault={handleSubmit}>
        <div class="form-control w-full max-w-xs">
          <label class="label" for="item-type">
            <span class="label-text">Tipo de Item</span>
          </label>
          <select
            id="item-type"
            class="select select-bordered"
            bind:value={selectedType}
          >
            <option value="note">Nota</option>
            <option value="task">Tarefa</option>
            <option value="link">Link</option>
          </select>
        </div>

        {#if selectedType === "note" || selectedType === "task"}
          <fieldset class="fieldset">
            <legend class="label">Conteúdo</legend>
            <textarea
              name="textarea textarea-bordered"
              id=""
              placeholder="Escreva a sua nota ou tarefa aqui..."
              bind:value={content}
            ></textarea>
          </fieldset>
        {:else if selectedType === "link"}
          <fieldset class="fieldset">
            <legend class="label">URL</legend>
            <input
              type="url"
              class="input input-bordered w-full max-w-xs"
              placeholder="https://example.com"
              bind:value={content}
            />
          </fieldset>
        {/if}

        <button class="btn btn-primary w-full">Adicionar</button>
      </form>
    </div>
  </aside>
</div>

<style>
  :global(body) {
    font-family: "Inter", sans-serif;
  }
</style>
