import { describe, expect, it } from "vitest";
import type { UrbanismGraph } from "./metamodel";
import { buildExportFilename, graphToCsvString, graphToJsonString } from "./exportData";

function makeGraph(overrides: Partial<UrbanismGraph> = {}): UrbanismGraph {
  return {
    project_id: "p1",
    project_name: "Métropolis Test",
    organization: {},
    author: "Auteur",
    generated_at: "2026-01-01T00:00:00Z",
    model: "club-urba",
    nodes: [
      {
        id: "n1",
        type: "urbanism",
        entity_type: "metier",
        entity_type_label: "Métier",
        couche: "metier",
        couche_label: "Métier",
        couche_color: "#000",
        label: "Objet, avec virgule",
        position: { x: 0, y: 0 },
      },
    ],
    edges: [
      {
        id: "e1",
        source: "n1",
        target: "n1",
        relation_type: "définit",
        category: "metier",
        criticite: null,
        commentaire: null,
      },
    ],
    meta_layers: [],
    stats: {
      total_objects: 1,
      total_relations: 1,
      visible_objects: 1,
      visible_relations: 1,
      by_couche: {},
      by_relation_type: {},
    },
    analysis: {
      orphans: [],
      orphan_count: 0,
      critical_relations: [],
      critical_count: 0,
      inconsistencies: [],
      inconsistency_count: 0,
      isolated_couches: [],
    },
    relation_categories: {},
    relation_type_legend: [],
    cartography: {
      id: "cart1",
      name: "Urbanisme Technique",
      type: "urbanisme_technique",
      status: "draft",
      is_active: true,
      is_archived: false,
    },
    cartography_version: {
      id: "v1",
      version: "1.2",
      status: "draft",
      is_current: true,
    },
    ...overrides,
  };
}

describe("buildExportFilename", () => {
  it("includes project, cartography name and version", () => {
    const filename = buildExportFilename(makeGraph(), "json");
    expect(filename).toBe("métropolis-test-urbanisme-technique-v1.2.json");
  });

  it("falls back to defaults when cartography metadata is missing", () => {
    const filename = buildExportFilename(
      makeGraph({ cartography: undefined, cartography_version: undefined }),
      "csv"
    );
    expect(filename).toBe("métropolis-test-cartographie-v1.0.csv");
  });
});

describe("graphToJsonString", () => {
  it("serializes the full graph as pretty JSON", () => {
    const json = graphToJsonString(makeGraph());
    const parsed = JSON.parse(json);
    expect(parsed.project_name).toBe("Métropolis Test");
    expect(parsed.nodes).toHaveLength(1);
  });
});

describe("graphToCsvString", () => {
  it("produces two sections (objects then relations) with escaped values", () => {
    const csv = graphToCsvString(makeGraph());
    expect(csv).toContain("# Objets");
    expect(csv).toContain("# Relations");
    expect(csv).toContain('"Objet, avec virgule"');
    expect(csv).toContain("e1,n1,n1,définit,metier,");
  });
});
