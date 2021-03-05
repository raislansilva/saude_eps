SELECT faixa, vinculo, count(name), ano FROM
(SELECT partner.name as name,
       CASE
         WHEN extract(YEAR FROM age(TIMESTAMP '2018-12-31', partner.birthday)) <= 45
           THEN 'Menor ou Igual 45'
         WHEN extract(YEAR FROM age(TIMESTAMP '2018-12-31', partner.birthday)) >= 46
           THEN 'Maior ou Igual 46'
         END                                                              AS faixa,
       CASE
         WHEN partner.function = 'Magistrado'
           THEN 'Magistrado'
         WHEN partner.function = 'Servidor Carreira' OR
              partner.function = 'Cargo Comissionado' THEN 'Servidor' END as vinculo,
        date_part('year', consulta.create_date) as ano
FROM saude_atendimento_consulta AS consulta
--        JOIN saude_atendimento_consulta_saude_cid_subcategoria_rel
--             ON consulta.id = saude_atendimento_consulta_saude_cid_subcategoria_rel.saude_atendimento_consulta_id
--        JOIN saude_cid_subcategoria AS subcategoria ON subcategoria.id = saude_cid_subcategoria_id
--        JOIN saude_cid_categoria AS categoria ON subcategoria.categoria_id = categoria.id
       JOIN saude_paciente AS paciente ON paciente.id = consulta.paciente_id
       JOIN res_partner AS partner ON partner.id = paciente.partner_id
       JOIN tjpi_vinculo tv ON partner.id = tv.partner_id
WHERE date_part('year', consulta.create_date) :: BIGINT in (2017, 2018)
  AND partner.is_company = FALSE
  AND consulta.atestado = FALSE
  AND partner.function IN ('Magistrado', 'Servidor Carreira', 'Cargo Comissionado')
GROUP BY faixa, vinculo, partner.name, ano
/*HAVING
       (extract(YEAR FROM age(TIMESTAMP '2018-12-31', partner.birthday)) <= 45 AND date_part('year', consulta.create_date) :: BIGINT in (2017, 2018)) OR
   (date_part('year', consulta.create_date) :: BIGINT = 2017, 2018)*/
ORDER BY faixa, vinculo) as P
WHERE (ano != 2017 and faixa != 'Maior ou Igual 46') or (ano = 2017 and faixa = 'Menor ou Igual 45') or (ano = 2018 and faixa = 'Maior ou Igual 46')
GROUP BY faixa, vinculo, ano
HAVING count(name) >= 1
order by ano, faixa, vinculo;

