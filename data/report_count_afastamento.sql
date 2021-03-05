SELECT
  SUM(atestado.dias)                                AS dias_afastamento,
  COUNT(atestado.id)                                AS frequencia,
  CASE WHEN partner.function = 'Magistrado'
    THEN 'Magistrado'
  WHEN partner.function = 'Servidor Carreira' OR
       partner.function = 'Cargo Comissionado' THEN 'Servidor' END as vinculo
FROM saude_atendimento_atestado AS atestado
  JOIN saude_atendimento_atestado_saude_cid_subcategoria_rel ON atestado.id = saude_atendimento_atestado_id
  JOIN saude_cid_subcategoria AS subcategoria ON subcategoria.id = saude_cid_subcategoria_id
  JOIN saude_cid_categoria AS categoria ON subcategoria.categoria_id = categoria.id
  JOIN saude_atendimento_consulta AS consulta ON consulta.id = atestado.consulta_id
  JOIN saude_paciente AS paciente ON paciente.id = consulta.paciente_id
  JOIN res_partner AS partner ON partner.id = paciente.partner_id
  JOIN tjpi_vinculo tv ON partner.id = tv.partner_id
WHERE date_part('year', consulta.create_date) :: BIGINT = 2018 AND partner.is_company = FALSE AND
      partner.function IN ('Magistrado', 'Servidor Carreira', 'Cargo Comissionado') AND
      subcategoria.codigo not in ('Z763', 'Z761', 'Z762')
GROUP BY
  vinculo
ORDER BY vinculo, dias_afastamento;
