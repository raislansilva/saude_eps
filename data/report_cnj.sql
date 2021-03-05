-- Relatório Atestados
SELECT
nome,
cpf,
tipo
FROM
 (SELECT
  partner.name as nome,
  partner.cpf as cpf,
  partner.function as tipo
FROM saude_atendimento_consulta AS consulta
  JOIN saude_paciente AS paciente ON paciente.id = consulta.paciente_id
  JOIN res_partner AS partner ON partner.id = paciente.partner_id
  JOIN tjpi_vinculo tv ON partner.id = tv.partner_id
WHERE date_part('year', consulta.create_date) :: BIGINT = 2018 AND partner.is_company = FALSE AND consulta.atestado = FALSE AND
      (partner.function IN ('Magistrado', 'Servidor Carreira', 'Cargo Comissionado') or partner.function ilike 'Depend%') and tv.area is not NULL
GROUP BY
  partner.name, partner.cpf, partner.function
ORDER BY nome) as P