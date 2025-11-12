<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import type { Item } from "./types";

  // 1. O componente recebe o 'item' a ser exibido como uma "propriedade" (prop).
  export let item: Item;

  // 2. Criamos um "despachante de eventos" para comunicar com o componente pai.
  const dispatch = createEventDispatcher();

  function handleToggle() {
    // 3. Em vez de alterar os dados aqui, ele "avisa" o pai que uma tarefa foi alternada.
    dispatch("toggle", { id: item.id });
  }
</script>

<!-- O HTML é o mesmo de antes, mas agora está encapsulado e reutilizável -->
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h2 class="card-title capitalize">{item.type}</h2>

    {#if item.type === "note"}
      <p class="whitespace-pre-wrap">{item.content}</p>
    {:else if item.type === "task"}
      <div class="form-control">
        <label class="label cursor-pointer justify-start gap-4">
          <input
            type="checkbox"
            class="checkbox checkbox-primary"
            checked={item.completed}
            on:change={handleToggle}
          />
          <span class="label-text" class:line-through={item.completed}>
            {item.content}
          </span>
        </label>
      </div>
    {:else if item.type === "link"}
      <a
        href={item.content}
        target="_blank"
        rel="noopener noreferrer"
        class="link link-hover"
      >
        {item.content}
      </a>
    {/if}
  </div>
</div>
