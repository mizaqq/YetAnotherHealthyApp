import type { MealListItemDTO, GroupedMealViewModel } from "@/types";

/**
 * Groups meals by their eaten_at date
 * @param meals Array of meals to group
 * @returns Array of grouped meals by date, sorted descending (newest first)
 */
export function groupMealsByDate(meals: MealListItemDTO[]): GroupedMealViewModel[] {
  // Create a map of date -> meals
  const groupedMap = new Map<string, MealListItemDTO[]>();

  for (const meal of meals) {
    // Extract date part only (YYYY-MM-DD)
    const date = meal.eaten_at.split("T")[0];
    
    if (!date) {
      continue;
    }

    const existing = groupedMap.get(date);
    if (existing) {
      existing.push(meal);
    } else {
      groupedMap.set(date, [meal]);
    }
  }

  // Convert map to array and sort by date descending
  const grouped: GroupedMealViewModel[] = Array.from(groupedMap.entries())
    .map(([date, meals]) => ({
      date,
      meals: meals.sort((a, b) => 
        new Date(b.eaten_at).getTime() - new Date(a.eaten_at).getTime()
      ),
    }))
    .sort((a, b) => b.date.localeCompare(a.date));

  return grouped;
}

