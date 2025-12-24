<script lang="ts">
  import { createEventDispatcher } from "svelte";

  import type { Goal } from "./types";

  export let goal: Goal;

  const dispatch = createEventDispatcher();

  function notifyParentOfToggle(milestoneId: string) {
    dispatch("toggleMilestone", {
      goalId: goal.id,
      milestoneId: milestoneId,
    });
  }
</script>

<div class="p-4 bg-base-100 rounded-box shadow">
  <label for="goal-{goal.id}" class="font-medium text-base-content"
    >{goal.title}</label
  >

  <div class="space-y-2 mt-2">
    {#each goal.milestones as milestone (milestone.id)}
      <div class="form-control">
        <label class="label cursor-pointer justify-start gap-3">
          <input
            type="checkbox"
            id="milestone-{milestone.id}"
            class="checkbox checkbox-primary"
            checked={milestone.completed}
            on:change={() => notifyParentOfToggle(milestone.id)}
          />
          <span class="label-text" class:line-through={milestone.completed}>
            {milestone.title}
          </span>
        </label>
      </div>
    {/each}
  </div>
</div>
