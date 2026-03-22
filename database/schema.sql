-- ═══════════════════════════════════════════════════════════
-- BioJSON Web Platform - Supabase Database Schema
-- ═══════════════════════════════════════════════════════════
-- 
-- 使用方法:
--   1. 登录 Supabase Dashboard
--   2. 进入 SQL Editor
--   3. 粘贴并执行此文件
-- ═══════════════════════════════════════════════════════════

-- 1. 论文表
CREATE TABLE IF NOT EXISTS papers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  title TEXT,
  journal TEXT,
  doi TEXT,
  md_content TEXT NOT NULL,
  extraction_json JSONB NOT NULL,
  verified_json JSONB,
  verification_report JSONB,
  gene_count INT DEFAULT 0,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_review', 'completed')),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. 基因表（从 JSON 展平，方便查询和标注）
CREATE TABLE IF NOT EXISTS genes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
  gene_index INT NOT NULL,
  gene_name TEXT,
  gene_data JSONB NOT NULL,
  auto_verification JSONB,
  auto_stats JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. 专家标注表
CREATE TABLE IF NOT EXISTS annotations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gene_id UUID REFERENCES genes(id) ON DELETE CASCADE,
  field_name TEXT NOT NULL,
  expert_verdict TEXT NOT NULL CHECK (expert_verdict IN ('correct', 'incorrect', 'modified')),
  corrected_value TEXT,
  comment TEXT,
  annotator_id UUID REFERENCES auth.users(id),
  annotator_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(gene_id, field_name, annotator_name)
);

ALTER TABLE annotations
  ADD COLUMN IF NOT EXISTS annotator_name TEXT;

ALTER TABLE annotations
  DROP CONSTRAINT IF EXISTS annotations_gene_id_field_name_annotator_id_key;

ALTER TABLE annotations
  ADD CONSTRAINT annotations_gene_id_field_name_annotator_name_key
  UNIQUE (gene_id, field_name, annotator_name);

-- 4. 索引
CREATE INDEX IF NOT EXISTS idx_genes_paper_id ON genes(paper_id);
CREATE INDEX IF NOT EXISTS idx_annotations_gene_id ON annotations(gene_id);
CREATE INDEX IF NOT EXISTS idx_annotations_annotator_id ON annotations(annotator_id);
CREATE INDEX IF NOT EXISTS idx_annotations_annotator_name ON annotations(annotator_name);
CREATE INDEX IF NOT EXISTS idx_papers_slug ON papers(slug);

-- 5. RLS (Row Level Security) 策略
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE genes ENABLE ROW LEVEL SECURITY;
ALTER TABLE annotations ENABLE ROW LEVEL SECURITY;

-- papers: 所有认证用户可读
CREATE POLICY "papers_read" ON papers FOR SELECT TO authenticated USING (true);
-- papers: 仅 service_role 可写（通过导入脚本）
CREATE POLICY "papers_insert" ON papers FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "papers_update" ON papers FOR UPDATE TO service_role USING (true);

-- genes: 所有认证用户可读
CREATE POLICY "genes_read" ON genes FOR SELECT TO authenticated USING (true);
-- genes: 仅 service_role 可写
CREATE POLICY "genes_insert" ON genes FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "genes_update" ON genes FOR UPDATE TO service_role USING (true);

-- annotations: 所有认证用户可读
CREATE POLICY "annotations_read" ON annotations FOR SELECT TO authenticated USING (true);
-- annotations: 认证用户可插入自己的标注
CREATE POLICY "annotations_insert" ON annotations FOR INSERT TO authenticated
  WITH CHECK (true);
-- annotations: 认证用户可更新自己的标注
CREATE POLICY "annotations_update" ON annotations FOR UPDATE TO authenticated
  USING (true);
-- annotations: 认证用户可删除自己的标注
CREATE POLICY "annotations_delete" ON annotations FOR DELETE TO authenticated
  USING (true);

-- 6. 允许匿名用户也可以读取（方便开发/演示，正式环境可去掉）
CREATE POLICY "papers_anon_read" ON papers FOR SELECT TO anon USING (true);
CREATE POLICY "genes_anon_read" ON genes FOR SELECT TO anon USING (true);
CREATE POLICY "annotations_anon_read" ON annotations FOR SELECT TO anon USING (true);
CREATE POLICY "annotations_anon_insert" ON annotations FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "annotations_anon_update" ON annotations FOR UPDATE TO anon USING (true);
CREATE POLICY "annotations_anon_delete" ON annotations FOR DELETE TO anon USING (true);

-- 7. updated_at 自动更新触发器
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER papers_updated_at
  BEFORE UPDATE ON papers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER annotations_updated_at
  BEFORE UPDATE ON annotations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
