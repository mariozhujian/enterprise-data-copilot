package cn.example.enterprisedatacopilot.dto;

/**
 * 为什么要用 AnalysisResult？
 *  因为真正的企业 Agent 不能总返回一大段自然语言，不能把模型生成的结果直接当作可信 SQL 或授权依据
 * @param intent
 * @param metric
 * @param timeRange
 * @param explanation
 */
public record AnalysisResult(
        String intent,

        String metric,

        String timeRange,

        String explanation
) {
}
