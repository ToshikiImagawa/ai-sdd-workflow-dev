<section class="decision-card" id="{decision_anchor}">
  <div class="decision-header">
    <span class="decision-badge">決定</span>
    <h2 class="decision-title">{decision_title}</h2>
  </div>
  <p class="decision-meta">{decision_date}</p>
  <p class="decision-rationale"><strong>理由:</strong> {decision_rationale}</p>
  <table class="alternatives-comparison">
    <thead>
      <tr><th>選択肢</th><th>概要</th><th>理由</th><th>判定</th></tr>
    </thead>
    <tbody>
{alternative_rows}
    </tbody>
  </table>
</section>
