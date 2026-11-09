import { describe, expect, it } from 'vitest';
import { store, initialProject } from '../../src/frontend/store';
function test_ac_8_history_persistence() {
  store.getState().load(initialProject());
  const before = structuredClone(store.getState().project);
  store.getState().edit(p => { p.master_bus.stereo_width = 0.4; });
  store.getState().undo(); expect(store.getState().project).toEqual(before);
  store.getState().redo(); expect(store.getState().project.master_bus.stereo_width).toBe(.4);
  store.getState().undo(); store.getState().edit(p => { p.master_bus.tape_drive = 1.5; });
  expect(store.getState().future).toHaveLength(0);
  store.getState().save(); store.getState().restore();
  expect(store.getState().project.master_bus.tape_drive).toBe(1.5);
  expect(JSON.parse(localStorage.getItem('k1-project')!)).not.toHaveProperty('past');
}
describe('SPEC-004 project history', () => { it('test_ac_8_history_persistence', test_ac_8_history_persistence); });
